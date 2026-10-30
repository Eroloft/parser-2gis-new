"""Check website reachability, HTTPS, and rough modernity signals.

Uses only stdlib by default. Optional httpx for better concurrency/timeouts.
"""

from __future__ import annotations

import re
import socket
import ssl
from dataclasses import dataclass, field
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

_USER_AGENT = (
    'Mozilla/5.0 (compatible; Parser2GIS-Enricher/2.0; +https://github.com/Eroloft/parser-2gis-new)'
)

# Modernity heuristics (cheap, no full browser)
_MODERN_SIGNALS = [
    (re.compile(r'<meta[^>]+name=["\']viewport["\']', re.I), 15, 'viewport'),
    (re.compile(r'rel=["\']canonical["\']', re.I), 5, 'canonical'),
    (re.compile(r'og:title|twitter:card', re.I), 5, 'og'),
    (re.compile(r'application/ld\+json', re.I), 5, 'jsonld'),
    (re.compile(r'wp-content|wordpress', re.I), 0, 'wordpress'),  # neutral
    (re.compile(r'react|__NEXT_DATA__|nuxt|vue\.|angular', re.I), 20, 'spa_fw'),
    (re.compile(r'tailwind|bootstrap\.min\.css|bulma', re.I), 10, 'css_fw'),
    (re.compile(r'cloudflare|cdn\.jsdelivr|unpkg\.com', re.I), 5, 'cdn'),
    (re.compile(r'content=["\'][^"\']*charset=utf-8', re.I), 5, 'utf8'),
]
_OUTDATED_SIGNALS = [
    (re.compile(r'jquery[-.]1\.[0-7]', re.I), -15, 'old_jquery'),
    (re.compile(r'<frameset|<font\s', re.I), -20, 'legacy_html'),
    (re.compile(r'marquee|blink', re.I), -25, 'ancient'),
]


@dataclass
class WebsiteReport:
    url: str = ''
    ok: bool = False
    status_code: Optional[int] = None
    final_url: str = ''
    https: bool = False
    ssl_ok: bool = False
    reachable: bool = False
    modernity_score: int = 0  # 0..100-ish
    modernity_label: str = 'unknown'  # modern / average / outdated / dead
    signals: list[str] = field(default_factory=list)
    error: str = ''
    title: str = ''

    def as_dict(self) -> dict:
        return {
            'site_ok': self.ok,
            'site_status': self.status_code or '',
            'site_final_url': self.final_url,
            'site_https': self.https,
            'site_ssl_ok': self.ssl_ok,
            'site_modernity_score': self.modernity_score,
            'site_modernity': self.modernity_label,
            'site_signals': ';'.join(self.signals),
            'site_error': self.error,
            'site_title': self.title,
        }


class WebsiteChecker:
    def __init__(self, timeout: float = 8.0, max_bytes: int = 120_000):
        self.timeout = timeout
        self.max_bytes = max_bytes

    def check(self, url: str) -> WebsiteReport:
        report = WebsiteReport(url=url or '')
        if not url:
            report.error = 'empty'
            report.modernity_label = 'none'
            return report

        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            report.url = url

        report.https = url.lower().startswith('https://')
        try:
            req = Request(url, headers={'User-Agent': _USER_AGENT}, method='GET')
            with urlopen(req, timeout=self.timeout, context=ssl.create_default_context()) as resp:
                report.status_code = getattr(resp, 'status', None) or resp.getcode()
                report.final_url = resp.geturl() or url
                report.https = report.final_url.lower().startswith('https://')
                report.ssl_ok = report.https
                report.reachable = True
                raw = resp.read(self.max_bytes)
                # Try decode
                charset = 'utf-8'
                ct = resp.headers.get('Content-Type', '')
                m = re.search(r'charset=([\w-]+)', ct, re.I)
                if m:
                    charset = m.group(1)
                try:
                    html = raw.decode(charset, errors='replace')
                except Exception:
                    html = raw.decode('utf-8', errors='replace')
        except HTTPError as e:
            report.status_code = e.code
            report.reachable = e.code < 500
            report.error = f'HTTP {e.code}'
            try:
                html = e.read(self.max_bytes).decode('utf-8', errors='replace')
            except Exception:
                html = ''
        except (URLError, socket.timeout, ssl.SSLError, OSError) as e:
            report.error = str(e)[:120]
            report.reachable = False
            report.modernity_label = 'dead'
            # Retry http if https failed
            if url.startswith('https://'):
                return self._try_http_fallback(url, report)
            return report
        except Exception as e:
            report.error = str(e)[:120]
            report.modernity_label = 'dead'
            return report

        report.ok = report.reachable and (report.status_code or 0) < 400
        self._score_html(html, report)
        return report

    def _try_http_fallback(self, https_url: str, report: WebsiteReport) -> WebsiteReport:
        http_url = 'http://' + https_url[8:]
        try:
            req = Request(http_url, headers={'User-Agent': _USER_AGENT}, method='GET')
            with urlopen(req, timeout=self.timeout) as resp:
                report.status_code = resp.getcode()
                report.final_url = resp.geturl() or http_url
                report.reachable = True
                report.https = False
                report.ssl_ok = False
                html = resp.read(self.max_bytes).decode('utf-8', errors='replace')
                report.ok = (report.status_code or 0) < 400
                self._score_html(html, report)
                report.signals.append('http_only')
                report.modernity_score = max(0, report.modernity_score - 20)
                self._label(report)
        except Exception as e:
            report.error = (report.error + '; ' + str(e)[:80]).strip('; ')
            report.modernity_label = 'dead'
        return report

    def _score_html(self, html: str, report: WebsiteReport) -> None:
        if not html:
            report.modernity_label = 'unknown'
            return
        score = 30 if report.https and report.ssl_ok else 10
        if report.ok:
            score += 10
        for rx, pts, name in _MODERN_SIGNALS:
            if rx.search(html):
                score += pts
                report.signals.append(name)
        for rx, pts, name in _OUTDATED_SIGNALS:
            if rx.search(html):
                score += pts
                report.signals.append(name)
        # Title
        tm = re.search(r'<title[^>]*>([^<]{1,120})</title>', html, re.I)
        if tm:
            report.title = re.sub(r'\s+', ' ', tm.group(1)).strip()[:100]
        report.modernity_score = max(0, min(100, score))
        self._label(report)

    def _label(self, report: WebsiteReport) -> None:
        if not report.reachable:
            report.modernity_label = 'dead'
        elif report.modernity_score >= 60:
            report.modernity_label = 'modern'
        elif report.modernity_score >= 35:
            report.modernity_label = 'average'
        else:
            report.modernity_label = 'outdated'
