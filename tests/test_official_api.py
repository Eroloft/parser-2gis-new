from __future__ import annotations

import pytest
from requests import RequestException

from parser_2gis.chrome import ChromeOptions
from parser_2gis.parser import ParserOptions, get_parser
from parser_2gis.parser.exceptions import ParserException
from parser_2gis.parser.parsers.official_api import OfficialApiParser


class _Writer:
    def __init__(self):
        self.docs = []

    def write(self, document):
        self.docs.append(document)


def _item(item_id='123_branch', name='Тестовая аптека'):
    return {
        'id': item_id,
        'locale': 'ru_RU',
        'type': 'branch',
        'name': name,
        'address_name': 'Москва, Тестовая улица, 1',
    }


def test_factory_uses_official_api_without_starting_chrome():
    options = ParserOptions(api_key='secret')

    parser = get_parser(
        'https://2gis.ru/moscow/search/Аптеки',
        ChromeOptions(),
        options,
    )

    assert isinstance(parser, OfficialApiParser)
    parser.close()


def test_official_api_search_reuses_original_document_shape(monkeypatch):
    calls = []
    responses = [
        {
            'meta': {'code': 200},
            'result': {'items': [{'id': '4500', 'name': 'Москва'}], 'total': 1},
        },
        {
            'meta': {'code': 200},
            'result': {'items': [_item()], 'total': 1},
        },
    ]
    parser = OfficialApiParser(
        'https://2gis.ru/moscow/search/%D0%90%D0%BF%D1%82%D0%B5%D0%BA%D0%B8/rubricId/211',
        ParserOptions(api_key='secret', max_records=10),
    )

    def fake_request(endpoint, params):
        calls.append((endpoint, params))
        return responses.pop(0)

    monkeypatch.setattr(parser, '_request', fake_request)
    writer = _Writer()
    parser.parse(writer)
    parser.close()

    assert calls[0] == ('items', {
        'q': 'Москва', 'type': 'adm_div.city', 'page_size': 10,
    })
    assert calls[1][0] == 'items'
    assert calls[1][1]['q'] == 'Аптеки'
    assert calls[1][1]['city_id'] == '4500'
    assert calls[1][1]['rubric_id'] == '211'
    assert calls[1][1]['type'] == 'branch'
    assert writer.docs == [{
        'meta': {'code': 200},
        'result': {'items': [_item()]},
    }]


def test_official_api_firm_uses_byid(monkeypatch):
    parser = OfficialApiParser(
        'https://2gis.ru/moscow/firm/70000001012345678',
        ParserOptions(api_key='secret'),
    )
    calls = []

    def fake_request(endpoint, params):
        calls.append((endpoint, params))
        return {'meta': {'code': 200}, 'result': {'items': [_item()]}}

    monkeypatch.setattr(parser, '_request', fake_request)
    writer = _Writer()
    parser.parse(writer)
    parser.close()

    assert calls[0][0] == 'items/byid'
    assert calls[0][1]['id'] == '70000001012345678'
    assert len(writer.docs) == 1


def test_network_error_does_not_expose_api_key(monkeypatch):
    class BrokenSession:
        def get(self, *args, **kwargs):
            raise RequestException('request URL contains super-secret-key')

        def close(self):
            pass

    parser = OfficialApiParser(
        'https://2gis.ru/moscow/search/Аптеки',
        ParserOptions(api_key='super-secret-key'),
    )
    parser._session.close()
    parser._session = BrokenSession()

    with pytest.raises(ParserException) as error:
        parser._request('items', {'q': 'Москва'})

    assert 'super-secret-key' not in str(error.value)
    parser.close()
