"""Deduplicate establishments by id, name+address, name+phone, and optional history."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional


def _norm_text(s: str) -> str:
    if not s:
        return ''
    s = s.lower().strip()
    s = re.sub(r'[«»"\'`]', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s


def _norm_phone(s: str) -> str:
    if not s:
        return ''
    return re.sub(r'\D', '', s)[-10:]  # last 10 digits


def _norm_addr(s: str) -> str:
    s = _norm_text(s)
    s = re.sub(r'\b(ул\.?|улица|пр\.?|проспект|пер\.?|переулок|д\.?|дом)\b', '', s)
    s = re.sub(r'[.,]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


@dataclass
class DedupOptions:
    by_id: bool = True
    by_name_address: bool = True
    by_name_phone: bool = True
    by_phone_only: bool = False  # aggressive: same phone = same place
    history_path: Optional[str] = None  # jsonl of previous keys
    skip_seen_in_history: bool = False


@dataclass
class Deduplicator:
    options: DedupOptions = field(default_factory=DedupOptions)
    _seen: set[str] = field(default_factory=set, init=False)
    _history: set[str] = field(default_factory=set, init=False)

    def __post_init__(self) -> None:
        if self.options.history_path and self.options.skip_seen_in_history:
            self._load_history()

    def _load_history(self) -> None:
        path = Path(self.options.history_path or '')
        if not path.is_file():
            return
        try:
            with path.open(encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        if isinstance(obj, str):
                            self._history.add(obj)
                        elif isinstance(obj, dict) and 'key' in obj:
                            self._history.add(obj['key'])
                    except json.JSONDecodeError:
                        self._history.add(line)
        except OSError:
            pass

    def save_history(self, keys: Iterable[str]) -> None:
        if not self.options.history_path:
            return
        path = Path(self.options.history_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a', encoding='utf-8') as f:
            for k in keys:
                if k not in self._history:
                    f.write(json.dumps({'key': k}, ensure_ascii=False) + '\n')
                    self._history.add(k)

    def keys_for(self, record: dict[str, Any]) -> list[str]:
        """Return fingerprint keys for a flat record (from extract_record + enrich)."""
        keys: list[str] = []
        rid = str(record.get('id') or record.get('item_id') or record.get('firm_id') or '')
        if self.options.by_id and rid:
            keys.append(f'id:{rid}')

        name = _norm_text(str(record.get('name') or ''))
        addr = _norm_addr(str(record.get('address') or ''))
        phone = _norm_phone(
            str(record.get('phone') or '')
            or (record.get('phones') or [''])[0] if isinstance(record.get('phones'), list) else ''
        )
        # contacts may be nested
        contacts = record.get('contacts') or {}
        if not phone and isinstance(contacts, dict):
            phone = _norm_phone(str(contacts.get('phone') or ''))

        if self.options.by_name_address and name and addr:
            keys.append(f'na:{name}|{addr}')
        if self.options.by_name_phone and name and phone:
            keys.append(f'np:{name}|{phone}')
        if self.options.by_phone_only and phone and len(phone) >= 10:
            keys.append(f'p:{phone}')

        if not keys and name:
            keys.append(f'n:{name}')
        return keys

    def is_duplicate(self, record: dict[str, Any]) -> bool:
        keys = self.keys_for(record)
        if not keys:
            return False
        if self.options.skip_seen_in_history and any(k in self._history for k in keys):
            return True
        if any(k in self._seen for k in keys):
            return True
        for k in keys:
            self._seen.add(k)
        return False

    def filter(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        new_keys: list[str] = []
        for r in records:
            if self.is_duplicate(r):
                continue
            out.append(r)
            new_keys.extend(self.keys_for(r))
        if self.options.history_path:
            self.save_history(new_keys)
        return out

    @staticmethod
    def stable_hash(record: dict[str, Any]) -> str:
        raw = json.dumps(
            {k: record.get(k) for k in ('name', 'address', 'phone', 'id')},
            ensure_ascii=False, sort_keys=True,
        )
        return hashlib.sha1(raw.encode()).hexdigest()[:12]
