from __future__ import annotations

import json
import os
import tempfile
import webbrowser
from functools import lru_cache
from typing import Any

from ..config import Configuration
from ..logger import logger
from ..paths import data_path
from ..writer import WriterOptions, get_writer
from .history import History
from .job import ParseJob

# Download file names per format.
_DOWNLOAD_NAMES = {'csv': '2gis.csv', 'xlsx': '2gis.xlsx',
                   'json': '2gis.json', 'html': '2gis.html'}

# Country code -> human name (for the link generator).
COUNTRIES = {
    'ru': 'Россия', 'kz': 'Казахстан', 'by': 'Беларусь', 'az': 'Азербайджан',
    'kg': 'Киргизия', 'uz': 'Узбекистан', 'cz': 'Чехия', 'eg': 'Египет',
    'it': 'Италия', 'sa': 'Саудовская Аравия', 'cy': 'Кипр', 'ae': 'ОАЭ',
    'cl': 'Чили', 'qa': 'Катар', 'om': 'Оман', 'bh': 'Бахрейн',
    'kw': 'Кувейт', 'iq': 'Ирак',
}


@lru_cache(maxsize=1)
def _load_cities() -> list[dict[str, Any]]:
    with open(data_path() / 'cities.json', 'r', encoding='utf-8') as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _load_rubrics() -> list[dict[str, Any]]:
    """Flat list of rubrics for the web generator picker."""
    with open(data_path() / 'rubrics.json', 'r', encoding='utf-8') as f:
        rubrics = json.load(f)
    out = []
    for node in rubrics.values():
        # Skip the synthetic root and group headers without a usable label.
        if node.get('code') in (None, '0') or not node.get('label'):
            continue
        out.append({
            'code': node['code'],
            'label': node['label'],
            'is_russian': bool(node.get('isRussian', True)),
            'is_non_russian': bool(node.get('isNonRussian', True)),
        })
    out.sort(key=lambda r: r['label'].lower())
    return out


def _build_config(data: dict[str, Any]) -> Configuration:
    """Build a Configuration from the web request payload."""
    config = Configuration()
    config.chrome.headless = bool(data.get('headless', True))
    config.parser.max_records = max(1, int(data.get('max_records', 100)))
    config.writer.csv.clean = bool(data.get('clean', True))

    adv = data.get('advanced', {}) or {}
    if adv:
        config.chrome.disable_images = bool(adv.get('disable_images', config.chrome.disable_images))
        config.chrome.start_maximized = bool(adv.get('start_maximized', config.chrome.start_maximized))
        if adv.get('memory_limit'):
            config.chrome.memory_limit = max(1, int(adv['memory_limit']))
        config.parser.skip_404_response = bool(adv.get('skip_404_response', config.parser.skip_404_response))
        config.parser.delay_between_clicks = max(0, int(adv.get('delay_between_clicks', 0) or 0))
        config.writer.csv.add_rubrics = bool(adv.get('add_rubrics', config.writer.csv.add_rubrics))
        config.writer.csv.add_comments = bool(adv.get('add_comments', config.writer.csv.add_comments))
        config.writer.csv.remove_empty_columns = bool(adv.get('remove_empty_columns', config.writer.csv.remove_empty_columns))
        config.writer.csv.remove_duplicates = bool(adv.get('remove_duplicates', config.writer.csv.remove_duplicates))
        if adv.get('columns_per_entity'):
            config.writer.csv.columns_per_entity = min(5, max(1, int(adv['columns_per_entity'])))
        if adv.get('encoding'):
            config.writer.encoding = str(adv['encoding'])

    f = data.get('filters', {}) or {}
    config.filters.dedup_franchises = bool(f.get('dedup_franchises'))
    config.filters.require_phone = bool(f.get('require_phone'))
    config.filters.require_whatsapp = bool(f.get('require_whatsapp'))
    config.filters.require_social = bool(f.get('require_social'))
    config.filters.require_email = bool(f.get('require_email'))
    config.filters.require_website = bool(f.get('require_website'))
    config.filters.min_rating = float(f.get('min_rating', 0) or 0)
    config.filters.min_reviews = int(f.get('min_reviews', 0) or 0)
    return config


def create_app():
    """Create the Flask app for the dashboard. Requires the `web` extra."""
    try:
        from flask import Flask, jsonify, request, send_file, send_from_directory
    except ImportError as e:  # pragma: no cover
        raise ImportError(
            'Для веб-интерфейса нужен Flask. Установите: pip install "parser-2gis[web]"'
        ) from e

    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    app = Flask(__name__, static_folder=static_dir, static_url_path='/static')
    job = ParseJob()
    history = History()

    def _export_send(docs, writer_opts: WriterOptions, fmt: str):
        """Write `docs` to a temp file in `fmt` and send it as a download."""
        tmp_dir = tempfile.mkdtemp(prefix='p2gis_web_')
        out_path = os.path.join(tmp_dir, _DOWNLOAD_NAMES[fmt])
        with get_writer(out_path, fmt, writer_opts) as writer:
            for doc in docs:
                writer.write(doc)
        return send_file(out_path, as_attachment=True, download_name=_DOWNLOAD_NAMES[fmt])

    @app.route('/')
    def index():
        return send_from_directory(static_dir, 'index.html')

    @app.route('/api/start', methods=['POST'])
    def api_start():
        data = request.get_json(force=True, silent=True) or {}
        urls = [u.strip() for u in (data.get('urls') or []) if u and u.strip()]
        if not urls:
            return jsonify({'ok': False, 'error': 'Не указаны ссылки'}), 400
        try:
            config = _build_config(data)
            job.start(config, urls)
        except RuntimeError as e:
            return jsonify({'ok': False, 'error': str(e)}), 409
        except Exception as e:
            logger.error('Не удалось запустить парсинг: %s', e)
            return jsonify({'ok': False, 'error': str(e)}), 400
        return jsonify({'ok': True})

    @app.route('/api/stop', methods=['POST'])
    def api_stop():
        job.stop()
        return jsonify({'ok': True})

    @app.route('/api/status')
    def api_status():
        cursor = request.args.get('cursor', default=0, type=int)
        logs = job.logs[cursor:]
        return jsonify({
            'status': job.status,
            'running': job.running,
            'count': job.count,
            'error': job.error,
            'logs': logs,
            'cursor': cursor + len(logs),
        })

    @app.route('/api/results')
    def api_results():
        return jsonify({'records': job.results()})

    @app.route('/api/generator')
    def api_generator():
        """Data for the link generator: countries, cities, rubrics."""
        cities = [
            {'name': c['name'], 'code': c['code'], 'domain': c['domain'],
             'country_code': c['country_code']}
            for c in _load_cities()
        ]
        countries = [{'code': k, 'name': v} for k, v in COUNTRIES.items()]
        countries.sort(key=lambda c: c['name'])
        return jsonify({'countries': countries, 'cities': cities, 'rubrics': _load_rubrics()})

    @app.route('/api/download')
    def api_download():
        fmt = request.args.get('format', 'csv')
        if fmt not in _DOWNLOAD_NAMES:
            return jsonify({'ok': False, 'error': 'Неизвестный формат'}), 400
        if not job.count:
            return jsonify({'ok': False, 'error': 'Нет данных'}), 400

        try:
            assert job.collector is not None
            return _export_send(job.collector.docs, job.collector._options, fmt)
        except Exception as e:
            logger.error('Ошибка экспорта: %s', e)
            return jsonify({'ok': False, 'error': str(e)}), 500

    @app.route('/api/history')
    def api_history():
        return jsonify({'items': history.list()})

    @app.route('/api/history/<hid>/results')
    def api_history_results(hid):
        docs = history.docs(hid)
        if docs is None:
            return jsonify({'ok': False, 'error': 'Запись не найдена'}), 404
        return jsonify({'records': history.records(hid)})

    @app.route('/api/history/<hid>/download')
    def api_history_download(hid):
        fmt = request.args.get('format', 'csv')
        if fmt not in _DOWNLOAD_NAMES:
            return jsonify({'ok': False, 'error': 'Неизвестный формат'}), 400
        docs = history.docs(hid)
        if not docs:
            return jsonify({'ok': False, 'error': 'Запись не найдена'}), 404
        try:
            opts = WriterOptions(**history.writer_options(hid))
        except Exception:
            opts = WriterOptions()
        try:
            return _export_send(docs, opts, fmt)
        except Exception as e:
            logger.error('Ошибка экспорта истории: %s', e)
            return jsonify({'ok': False, 'error': str(e)}), 500

    @app.route('/api/history/<hid>', methods=['DELETE'])
    def api_history_delete(hid):
        return jsonify({'ok': history.delete(hid)})

    return app


def run_server(host: str = '127.0.0.1', port: int = 8666, open_browser: bool = True) -> None:
    """Run the dashboard server (blocking)."""
    app = create_app()
    url = f'http://{host}:{port}/'
    logger.info('Веб-интерфейс запущен: %s', url)
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    app.run(host=host, port=port, threaded=True, debug=False, use_reloader=False)
