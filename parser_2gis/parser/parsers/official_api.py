from __future__ import annotations

import json
import re
import time
from functools import lru_cache
from typing import TYPE_CHECKING, Any
from urllib.parse import unquote, urlparse

import requests
from requests import RequestException

from ...logger import logger
from ...paths import data_path
from ..exceptions import ParserException

if TYPE_CHECKING:
    from ...writer import FileWriter
    from ..options import ParserOptions


_API_BASE = 'https://catalog.api.2gis.com/3.0'
_FIELDS = ','.join((
    'items.address',
    'items.adm_div',
    'items.contact_groups',
    'items.name_ex',
    'items.org',
    'items.point',
    'items.reviews',
    'items.rubrics',
    'items.schedule',
))


@lru_cache(maxsize=1)
def _city_names() -> dict[str, str]:
    with open(data_path() / 'cities.json', 'r', encoding='utf-8') as stream:
        cities = json.load(stream)
    return {str(city['code']).lower(): str(city['name']) for city in cities}


class OfficialApiParser:
    """Collect catalog documents through the documented 2GIS Places API.

    This transport is selected only when the user supplies an API key.  The
    returned documents are fed into the original project's writers and filters
    unchanged, preserving its data model and export behaviour.
    """

    def __init__(self, url: str, parser_options: ParserOptions) -> None:
        self._url = url
        self._options = parser_options
        self._api_key = parser_options.api_key.strip()
        self._session = requests.Session()
        self._closed = False

    def _request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        if self._closed:
            raise ParserException('Сбор остановлен пользователем.')
        safe_params = {**params, 'key': self._api_key}
        try:
            response = self._session.get(
                f'{_API_BASE}/{endpoint.lstrip("/")}',
                params=safe_params,
                timeout=(10, 30),
            )
        except RequestException as exc:
            # Never include the prepared URL: it contains the user's API key.
            raise ParserException(
                'Не удалось подключиться к официальному API 2GIS. '
                'Проверьте сеть и повторите позже.'
            ) from exc

        try:
            document = response.json()
        except ValueError as exc:
            raise ParserException(
                f'Официальный API 2GIS вернул не JSON (HTTP {response.status_code}).'
            ) from exc

        meta = document.get('meta') if isinstance(document, dict) else None
        error = meta.get('error') if isinstance(meta, dict) else None
        if response.status_code != 200 or error:
            message = error.get('message') if isinstance(error, dict) else None
            if response.status_code in (401, 403):
                message = 'ключ API отклонён или не имеет доступа к Places API'
            elif response.status_code == 429:
                message = 'превышен лимит запросов официального API'
            raise ParserException(
                f'Официальный API 2GIS вернул ошибку HTTP {response.status_code}'
                + (f': {message}' if message else '.')
            )
        if not isinstance(document, dict) or not isinstance(document.get('result'), dict):
            raise ParserException('Официальный API 2GIS вернул неожиданный документ.')
        return document

    @staticmethod
    def _path_parts(url: str) -> list[str]:
        return [unquote(part) for part in urlparse(url).path.split('/') if part]

    def _resolve_city_id(self, city_alias: str) -> str:
        city_name = _city_names().get(city_alias.lower())
        if not city_name:
            raise ParserException(
                f'Город «{city_alias}» отсутствует в справочнике Parser2GIS.'
            )
        document = self._request('items', {
            'q': city_name,
            'type': 'adm_div.city',
            'page_size': 10,
        })
        items = document['result'].get('items') or []
        exact = next(
            (item for item in items
             if str(item.get('name', '')).casefold() == city_name.casefold()),
            items[0] if items else None,
        )
        if not exact or not exact.get('id'):
            raise ParserException(
                f'Официальный API 2GIS не нашёл идентификатор города «{city_name}».'
            )
        return str(exact['id'])

    @staticmethod
    def _single_item_document(document: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
        return {
            'meta': document.get('meta', {'code': 200}),
            'result': {'items': [item]},
        }

    def _parse_firm(self, parts: list[str], writer: FileWriter) -> None:
        try:
            firm_id = parts[parts.index('firm') + 1]
        except (ValueError, IndexError) as exc:
            raise ParserException('В ссылке организации отсутствует идентификатор.') from exc
        document = self._request('items/byid', {
            'id': firm_id,
            'fields': _FIELDS,
        })
        items = document['result'].get('items') or []
        if not items:
            logger.warning('Организация не найдена официальным API 2GIS.')
            return
        writer.write(self._single_item_document(document, items[0]))

    def _parse_paged(self, params: dict[str, Any], writer: FileWriter) -> None:
        collected = 0
        page = 1
        page_size = min(50, self._options.max_records)
        while collected < self._options.max_records:
            document = self._request('items', {
                **params,
                'page': page,
                'page_size': page_size,
                'fields': _FIELDS,
            })
            result = document['result']
            items = result.get('items') or []
            if not items:
                break
            for item in items:
                if collected >= self._options.max_records:
                    break
                writer.write(self._single_item_document(document, item))
                collected += 1

            total = result.get('total')
            if isinstance(total, int) and collected >= total:
                break
            if not isinstance(total, int) and len(items) < page_size:
                break
            page += 1
            if self._options.delay_between_clicks:
                time.sleep(self._options.delay_between_clicks / 1000)
            if self._closed:
                raise ParserException('Сбор остановлен пользователем.')

        if collected >= self._options.max_records:
            logger.info('Собрано максимально разрешённое количество записей с данного URL.')

    def _parse_search(self, parts: list[str], writer: FileWriter) -> None:
        try:
            search_index = parts.index('search')
            city_alias = parts[0]
            query = parts[search_index + 1].strip()
        except (ValueError, IndexError) as exc:
            raise ParserException('В ссылке поиска отсутствует город или запрос.') from exc
        if not query:
            raise ParserException('В ссылке поиска отсутствует запрос.')
        params: dict[str, Any] = {
            'q': query,
            'city_id': self._resolve_city_id(city_alias),
            'type': 'branch',
        }
        try:
            rubric_index = parts.index('rubricId')
            rubric_id = re.match(r'\d+', parts[rubric_index + 1])
            if rubric_id:
                params['rubric_id'] = rubric_id.group(0)
        except (ValueError, IndexError):
            pass
        self._parse_paged(params, writer)

    def _parse_inside(self, parts: list[str], writer: FileWriter) -> None:
        try:
            inside_index = parts.index('inside')
            building_id = parts[inside_index + 1]
        except (ValueError, IndexError) as exc:
            raise ParserException('В ссылке здания отсутствует идентификатор.') from exc
        self._parse_paged({
            'building_id': building_id,
            'type': 'branch',
        }, writer)

    def parse(self, writer: FileWriter) -> None:
        logger.info('Используется официальный Places API 2GIS.')
        parts = self._path_parts(self._url)
        if 'firm' in parts:
            self._parse_firm(parts, writer)
        elif 'inside' in parts:
            self._parse_inside(parts, writer)
        elif 'search' in parts:
            self._parse_search(parts, writer)
        else:  # guarded by the parser factory; defensive for direct use
            raise ParserException('Тип ссылки не поддерживается официальным API 2GIS.')

    def close(self) -> None:
        self._closed = True
        self._session.close()

    def __enter__(self) -> OfficialApiParser:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
