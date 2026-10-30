"""Parallel enrichment pipeline: contacts + website check → flat columns for table."""

from __future__ import annotations

import concurrent.futures
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from .contacts import ContactFinder, NormalizedContacts
from .website import WebsiteChecker, WebsiteReport


@dataclass
class EnrichOptions:
    enabled: bool = True
    check_websites: bool = True
    scrape_site_for_contacts: bool = False  # needs network + HTML; off by default for speed
    max_workers: int = 8
    website_timeout: float = 8.0
    # Column prefixes / which extra fields to attach
    add_modernity: bool = True
    add_telegram: bool = True
    add_vk: bool = True
    add_whatsapp: bool = True


@dataclass
class Enricher:
    options: EnrichOptions = field(default_factory=EnrichOptions)
    finder: ContactFinder = field(default_factory=ContactFinder)
    checker: Optional[WebsiteChecker] = None

    def __post_init__(self) -> None:
        if self.checker is None:
            self.checker = WebsiteChecker(timeout=self.options.website_timeout)

    def enrich_one(self, record: dict[str, Any]) -> dict[str, Any]:
        """Mutate-copy a flat record (from extract_record) with enrichment fields."""
        if not self.options.enabled:
            return record

        out = dict(record)
        contacts_src = out.get('contacts') or {}
        if not isinstance(contacts_src, dict):
            contacts_src = {}

        nc = self.finder.from_2gis_contacts(contacts_src)

        # Optional: pull more from description / name (rarely useful)
        blob = ' '.join(filter(None, [
            str(out.get('name') or ''),
            str(out.get('description') or ''),
            str(out.get('address') or ''),
        ]))
        nc = self.finder.from_text(blob, nc)

        site_report: Optional[WebsiteReport] = None
        website = nc.website or contacts_src.get('website') or contacts_src.get('site')
        if website and self.options.check_websites and self.checker:
            site_report = self.checker.check(website)
            if self.options.scrape_site_for_contacts and site_report and site_report.reachable:
                # We don't keep full HTML in report; optional second fetch would be needed.
                # For now rely on title + already-found contacts. Full scrape can be added later.
                pass

        flat = nc.as_dict()
        # Prefer existing 2GIS phone/email if enricher found nothing extra
        if not flat.get('phone') and contacts_src.get('phone'):
            flat['phone'] = contacts_src['phone']
        if not flat.get('email') and contacts_src.get('email'):
            flat['email'] = contacts_src['email']
        if not flat.get('website') and website:
            flat['website'] = website

        out.update({
            'phone': flat.get('phone') or out.get('phone') or '',
            'email': flat.get('email') or '',
            'website': flat.get('website') or '',
            'telegram': flat.get('telegram') or '',
            'telegram_url': flat.get('telegram_url') or '',
            'vkontakte': flat.get('vkontakte') or '',
            'whatsapp': flat.get('whatsapp') or '',
            'instagram': flat.get('instagram') or '',
            'facebook': flat.get('facebook') or '',
        })

        if site_report and self.options.add_modernity:
            out.update(site_report.as_dict())
        else:
            out.setdefault('site_ok', '')
            out.setdefault('site_modernity', '')
            out.setdefault('site_modernity_score', '')

        return out

    def enrich_many(
        self,
        records: list[dict[str, Any]],
        progress: Optional[Callable[[int, int], None]] = None,
    ) -> list[dict[str, Any]]:
        if not self.options.enabled or not records:
            return list(records)

        n = len(records)
        workers = max(1, min(self.options.max_workers, n))
        results: list[Optional[dict[str, Any]]] = [None] * n

        def _job(idx: int) -> tuple[int, dict[str, Any]]:
            return idx, self.enrich_one(records[idx])

        done = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            futs = [pool.submit(_job, i) for i in range(n)]
            for fut in concurrent.futures.as_completed(futs):
                idx, rec = fut.result()
                results[idx] = rec
                done += 1
                if progress:
                    progress(done, n)

        return [r for r in results if r is not None]


def enrich_records(
    records: list[dict[str, Any]],
    options: Optional[EnrichOptions] = None,
    progress: Optional[Callable[[int, int], None]] = None,
) -> list[dict[str, Any]]:
    return Enricher(options=options or EnrichOptions()).enrich_many(records, progress=progress)


# Columns recommended for CSV/XLSX when enrichment is on
ENRICH_COLUMNS = [
    'name', 'description', 'rubrics', 'address', 'city',
    'rating', 'review_count',
    'phone', 'email', 'website',
    'telegram', 'telegram_url', 'vkontakte', 'whatsapp', 'instagram', 'facebook',
    'site_ok', 'site_status', 'site_https', 'site_modernity', 'site_modernity_score',
    'site_title', 'site_error',
    'url',
]
