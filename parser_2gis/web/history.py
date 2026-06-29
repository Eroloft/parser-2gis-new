from __future__ import annotations

import json
import pathlib
import re
from datetime import datetime
from typing import Any, Optional

from ..logger import logger
from ..paths import user_path
from ..writer.record import extract_record

# Keep at most this many past parses on disk.
_MAX_ENTRIES = 30
_ID_RE = re.compile(r'^[0-9\-]+$')


def _history_dir() -> pathlib.Path:
    d = user_path() / 'history'
    d.mkdir(parents=True, exist_ok=True)
    return d


class History:
    """Persisted parse history — one JSON file per completed parse.

    Stored under the user data dir so results survive page reloads and server
    restarts. Each entry keeps the raw catalog documents so it can be re-rendered
    as cards and re-exported to any format later.
    """
    def save(self, urls: list[str], docs: list[Any], writer_options: dict) -> Optional[str]:
        if not docs:
            return None
        hid = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        payload = {
            'id': hid,
            'created_at': datetime.now().isoformat(timespec='seconds'),
            'urls': urls,
            'count': len(docs),
            'writer': writer_options,
            'docs': docs,
        }
        try:
            with open(_history_dir() / f'{hid}.json', 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False)
            self._prune()
        except Exception as e:
            logger.error('Не удалось сохранить историю: %s', e)
            return None
        return hid

    def list(self) -> list[dict]:
        items = []
        for path in _history_dir().glob('*.json'):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    d = json.load(f)
                items.append({'id': d['id'], 'created_at': d.get('created_at'),
                              'urls': d.get('urls', []), 'count': d.get('count', 0)})
            except Exception:
                continue
        items.sort(key=lambda x: x['id'], reverse=True)
        return items

    def _load(self, hid: str) -> Optional[dict]:
        if not _ID_RE.match(hid or ''):  # guard against path traversal
            return None
        path = _history_dir() / f'{hid}.json'
        if not path.is_file():
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def docs(self, hid: str) -> Optional[list[Any]]:
        d = self._load(hid)
        return d.get('docs') if d else None

    def writer_options(self, hid: str) -> dict:
        d = self._load(hid)
        return (d or {}).get('writer', {}) or {}

    def records(self, hid: str) -> list[dict]:
        out = []
        for doc in (self.docs(hid) or []):
            record = extract_record(doc)
            if record:
                out.append(record)
        return out

    def delete(self, hid: str) -> bool:
        if not _ID_RE.match(hid or ''):
            return False
        path = _history_dir() / f'{hid}.json'
        try:
            if path.is_file():
                path.unlink()
                return True
        except Exception:
            pass
        return False

    def _prune(self) -> None:
        files = sorted(_history_dir().glob('*.json'), key=lambda p: p.name, reverse=True)
        for path in files[_MAX_ENTRIES:]:
            try:
                path.unlink()
            except Exception:
                pass
