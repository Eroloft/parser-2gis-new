"""Glue: take list of extract_record dicts → enrich → dedup → ready for table."""

from __future__ import annotations

from typing import Any, Callable, Optional

from ..writer.options import EnrichWriterOptions
from .dedup import Deduplicator, DedupOptions
from .enrich import EnrichOptions, Enricher


def run_enrichment(
    records: list[dict[str, Any]],
    opts: Optional[EnrichWriterOptions] = None,
    progress: Optional[Callable[[int, int], None]] = None,
) -> list[dict[str, Any]]:
    """Full post-process for table export.

    1. Contact normalization + optional website checks (parallel)
    2. Deduplication (name+address, name+phone, optional history)
    """
    opts = opts or EnrichWriterOptions()
    if not opts.enabled:
        return list(records)

    enrich_opts = EnrichOptions(
        enabled=True,
        check_websites=opts.check_websites,
        scrape_site_for_contacts=opts.scrape_site_for_contacts,
        max_workers=opts.max_workers,
        website_timeout=opts.website_timeout,
    )
    enriched = Enricher(options=enrich_opts).enrich_many(records, progress=progress)

    dedup_opts = DedupOptions(
        by_id=True,
        by_name_address=opts.dedup_name_address,
        by_name_phone=opts.dedup_name_phone,
        history_path=opts.dedup_history_path or None,
        skip_seen_in_history=opts.skip_seen_in_history,
    )
    return Deduplicator(options=dedup_opts).filter(enriched)
