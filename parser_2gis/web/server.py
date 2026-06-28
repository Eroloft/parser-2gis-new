from __future__ import annotations

import os
import tempfile
import webbrowser
from typing import Any

from ..config import Configuration
from ..logger import logger
from .job import ParseJob

# Download file names per format.
_DOWNLOAD_NAMES = {'csv': '2gis.csv', 'xlsx': '2gis.xlsx',
                   'json': '2gis.json', 'html': '2gis.html'}


def _build_config(data: dict[str, Any]) -> Configuration:
    """Build a Configuration from the web request payload."""
    config = Configuration()
    config.chrome.headless = bool(data.get('headless', True))
    config.parser.max_records = max(1, int(data.get('max_records', 100)))
    config.writer.csv.clean = bool(data.get('clean', True))

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

    @app.route('/api/download')
    def api_download():
        fmt = request.args.get('format', 'csv')
        if fmt not in _DOWNLOAD_NAMES:
            return jsonify({'ok': False, 'error': 'Неизвестный формат'}), 400
        if not job.count:
            return jsonify({'ok': False, 'error': 'Нет данных'}), 400

        tmp_dir = tempfile.mkdtemp(prefix='p2gis_web_')
        out_path = os.path.join(tmp_dir, _DOWNLOAD_NAMES[fmt])
        try:
            job.export(out_path, fmt)
        except Exception as e:
            logger.error('Ошибка экспорта: %s', e)
            return jsonify({'ok': False, 'error': str(e)}), 500
        return send_file(out_path, as_attachment=True, download_name=_DOWNLOAD_NAMES[fmt])

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
