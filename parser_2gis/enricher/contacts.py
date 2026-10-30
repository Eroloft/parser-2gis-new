"""Extract and normalize phones, Telegram, VK, email, website from 2GIS contacts
and optionally from website HTML (lightweight, no heavy browser)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional
from urllib.parse import urlparse, unquote

# International phone: keep digits, optional leading +
_PHONE_RE = re.compile(
    r'(?:\+?\d[\d\-\s().]{7,}\d)',
    re.UNICODE,
)
_TG_USER_RE = re.compile(
    r'(?:t\.me/|telegram\.me/|tg://resolve\?domain=)([a-zA-Z0-9_]{4,})',
    re.I,
)
_TG_HANDLE_RE = re.compile(r'(?<![@\w])@([a-zA-Z0-9_]{4,32})\b')
_VK_RE = re.compile(
    r'(?:vk\.com/|vkontakte\.ru/)([a-zA-Z0-9_.]+)',
    re.I,
)
_EMAIL_RE = re.compile(
    r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
)
_WA_RE = re.compile(
    r'(?:wa\.me/|api\.whatsapp\.com/send\?phone=)(\+?\d{10,15})',
    re.I,
)
_IG_RE = re.compile(r'(?:instagram\.com/)([a-zA-Z0-9._]+)', re.I)
_FB_RE = re.compile(r'(?:facebook\.com/|fb\.com/)([a-zA-Z0-9.]+)', re.I)


def _clean_phone(raw: str) -> Optional[str]:
    if not raw:
        return None
    digits = re.sub(r'[^\d+]', '', raw)
    if digits.startswith('00'):
        digits = '+' + digits[2:]
    # Russian local 8xxxxxxxxxx -> +7
    if digits.startswith('8') and len(digits) == 11:
        digits = '+7' + digits[1:]
    if digits.startswith('7') and len(digits) == 11:
        digits = '+' + digits
    if not digits.startswith('+') and len(digits) >= 10:
        digits = '+' + digits
    # Minimal length check
    pure = digits.lstrip('+')
    if len(pure) < 10 or len(pure) > 15:
        return None
    return digits


def _norm_url(url: str) -> Optional[str]:
    if not url:
        return None
    url = url.strip().split('?')[0].rstrip('/')
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    try:
        p = urlparse(url)
        if not p.netloc or '.' not in p.netloc:
            return None
        return f'{p.scheme}://{p.netloc}{p.path}'.rstrip('/')
    except Exception:
        return None


@dataclass
class NormalizedContacts:
    """Normalized contact set for one establishment."""

    phones: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    website: Optional[str] = None
    telegram: Optional[str] = None  # @handle or t.me link
    telegram_url: Optional[str] = None
    vkontakte: Optional[str] = None  # vk.com/...
    whatsapp: Optional[str] = None  # +digits or wa.me
    instagram: Optional[str] = None
    facebook: Optional[str] = None
    other_social: dict[str, str] = field(default_factory=dict)

    def primary_phone(self) -> Optional[str]:
        return self.phones[0] if self.phones else None

    def primary_email(self) -> Optional[str]:
        return self.emails[0] if self.emails else None

    def as_dict(self) -> dict[str, Any]:
        return {
            'phone': self.primary_phone() or '',
            'phones': self.phones,
            'email': self.primary_email() or '',
            'emails': self.emails,
            'website': self.website or '',
            'telegram': self.telegram or '',
            'telegram_url': self.telegram_url or '',
            'vkontakte': self.vkontakte or '',
            'whatsapp': self.whatsapp or '',
            'instagram': self.instagram or '',
            'facebook': self.facebook or '',
            **{f'social_{k}': v for k, v in self.other_social.items()},
        }


class ContactFinder:
    """Pull structured contacts from 2GIS contact groups + free text / HTML."""

    def from_2gis_contacts(self, contacts_map: dict[str, str]) -> NormalizedContacts:
        """contacts_map is the flat dict from extract_record (type -> value/url)."""
        out = NormalizedContacts()
        for ctype, val in (contacts_map or {}).items():
            if not val:
                continue
            ctype = (ctype or '').lower()
            if ctype == 'phone':
                p = _clean_phone(val)
                if p and p not in out.phones:
                    out.phones.append(p)
            elif ctype == 'email':
                e = val.strip().lower()
                if e and e not in out.emails:
                    out.emails.append(e)
            elif ctype in ('website', 'site'):
                out.website = _norm_url(val) or out.website
            elif ctype == 'telegram':
                self._add_tg(out, val)
            elif ctype in ('vkontakte', 'vk'):
                self._add_vk(out, val)
            elif ctype == 'whatsapp':
                self._add_wa(out, val)
            elif ctype == 'instagram':
                m = _IG_RE.search(val) or re.search(r'([a-zA-Z0-9._]+)$', val)
                if m:
                    out.instagram = f'https://instagram.com/{m.group(1)}'
            elif ctype == 'facebook':
                m = _FB_RE.search(val)
                if m:
                    out.facebook = f'https://facebook.com/{m.group(1)}'
            else:
                out.other_social[ctype] = val
        return out

    def from_text(self, text: str, base: Optional[NormalizedContacts] = None) -> NormalizedContacts:
        """Scan free text / HTML for extra contacts."""
        out = base or NormalizedContacts()
        if not text:
            return out

        for m in _PHONE_RE.finditer(text):
            p = _clean_phone(m.group(0))
            if p and p not in out.phones:
                out.phones.append(p)

        for m in _EMAIL_RE.finditer(text):
            e = m.group(0).lower()
            if e not in out.emails and not e.endswith(('.png', '.jpg', '.gif')):
                out.emails.append(e)

        for m in _TG_USER_RE.finditer(text):
            self._add_tg(out, m.group(0))
        for m in _TG_HANDLE_RE.finditer(text):
            handle = m.group(1)
            if handle.lower() not in ('http', 'https', 'www'):
                self._add_tg(out, f'@{handle}')

        for m in _VK_RE.finditer(text):
            self._add_vk(out, m.group(0))

        for m in _WA_RE.finditer(text):
            self._add_wa(out, m.group(1))

        for m in _IG_RE.finditer(text):
            if not out.instagram:
                out.instagram = f'https://instagram.com/{m.group(1)}'

        for m in _FB_RE.finditer(text):
            if not out.facebook:
                out.facebook = f'https://facebook.com/{m.group(1)}'

        # Rough website: first http(s) that is not a social network
        if not out.website:
            for m in re.finditer(r'https?://[^\s"\'<>]+', text, re.I):
                u = m.group(0).split('?')[0]
                low = u.lower()
                if any(x in low for x in (
                    't.me', 'telegram', 'vk.com', 'instagram', 'facebook',
                    'wa.me', 'youtube', 'twitter', 'ok.ru', '2gis.',
                )):
                    continue
                n = _norm_url(u)
                if n:
                    out.website = n
                    break
        return out

    def _add_tg(self, out: NormalizedContacts, val: str) -> None:
        if out.telegram:
            return
        val = unquote(val.strip())
        m = _TG_USER_RE.search(val)
        handle = m.group(1) if m else None
        if not handle and val.startswith('@'):
            handle = val[1:]
        if not handle and re.fullmatch(r'[a-zA-Z0-9_]{4,32}', val):
            handle = val
        if handle:
            out.telegram = f'@{handle}'
            out.telegram_url = f'https://t.me/{handle}'

    def _add_vk(self, out: NormalizedContacts, val: str) -> None:
        if out.vkontakte:
            return
        m = _VK_RE.search(val)
        if m:
            out.vkontakte = f'https://vk.com/{m.group(1)}'
        elif 'vk.com' in val or 'vkontakte' in val:
            out.vkontakte = _norm_url(val) or val

    def _add_wa(self, out: NormalizedContacts, val: str) -> None:
        if out.whatsapp:
            return
        m = _WA_RE.search(val)
        digits = m.group(1) if m else val
        p = _clean_phone(digits)
        if p:
            out.whatsapp = p
            if p not in out.phones:
                out.phones.append(p)
