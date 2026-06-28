from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from pydantic import ValidationError

from .models import CatalogItem
from .writers import FileWriter

if TYPE_CHECKING:
    from .options import FilterOptions

# Contact types treated as "social network / messenger" for `require_social`.
SOCIAL_TYPES = {
    'instagram', 'facebook', 'twitter', 'vkontakte', 'youtube', 'odnoklassniki',
    'telegram', 'whatsapp', 'viber', 'skype', 'linkedin', 'pinterest',
}


@dataclass
class _Features:
    """Filterable features extracted from a catalog document."""
    org_id: Optional[str]
    has_phone: bool
    has_whatsapp: bool
    has_social: bool
    has_email: bool
    has_website: bool
    rating: float
    reviews: int


def extract_features(catalog_doc: Any) -> Optional[_Features]:
    """Extract filterable features from a Catalog Item API document.

    Returns `None` if the document is malformed (let the inner writer report it).
    """
    try:
        item = catalog_doc['result']['items'][0]
        catalog_item = CatalogItem(**item)
    except (KeyError, IndexError, TypeError, ValidationError):
        return None

    contact_types = set()
    for group in catalog_item.contact_groups:
        for contact in group.contacts:
            contact_types.add(contact.type)

    rating = 0.0
    reviews = 0
    if catalog_item.reviews:
        rating = catalog_item.reviews.general_rating or 0.0
        reviews = catalog_item.reviews.general_review_count or 0

    return _Features(
        org_id=catalog_item.org.id if catalog_item.org else None,
        has_phone='phone' in contact_types,
        has_whatsapp='whatsapp' in contact_types,
        has_social=bool(contact_types & SOCIAL_TYPES),
        has_email='email' in contact_types,
        has_website='website' in contact_types,
        rating=rating,
        reviews=reviews,
    )


def any_filter_enabled(options: FilterOptions) -> bool:
    """Whether at least one filter is active (used to skip wrapping otherwise)."""
    return any([
        options.dedup_franchises, options.require_phone, options.require_whatsapp,
        options.require_social, options.require_email, options.require_website,
        options.min_rating > 0, options.min_reviews > 0,
    ])


class FilterWriter(FileWriter):
    """Writer decorator that applies record-level filters and franchise dedup.

    Wraps any `FileWriter`. Records failing the active filters are dropped before
    reaching the inner writer. With `dedup_franchises`, only the first surviving
    branch per organization is forwarded; because filters run before dedup, the
    kept branch is the first one that actually passes the filters (e.g. the first
    branch that has a phone).
    """
    def __init__(self, inner: FileWriter, options: FilterOptions) -> None:
        super().__init__(inner._file_path, inner._options)
        self._inner = inner
        self._filter_options = options
        self._seen_orgs: set[str] = set()

    def _passes(self, f: _Features) -> bool:
        o = self._filter_options
        if o.require_phone and not f.has_phone:
            return False
        if o.require_whatsapp and not f.has_whatsapp:
            return False
        if o.require_social and not f.has_social:
            return False
        if o.require_email and not f.has_email:
            return False
        if o.require_website and not f.has_website:
            return False
        if o.min_rating and f.rating < o.min_rating:
            return False
        if o.min_reviews and f.reviews < o.min_reviews:
            return False
        return True

    def write(self, catalog_doc: Any) -> None:
        features = extract_features(catalog_doc)
        if features is not None:
            if not self._passes(features):
                return
            if self._filter_options.dedup_franchises and features.org_id:
                if features.org_id in self._seen_orgs:
                    return
                self._seen_orgs.add(features.org_id)
        self._inner.write(catalog_doc)

    def __enter__(self) -> 'FilterWriter':
        self._inner.__enter__()
        return self

    def __exit__(self, *exc_info) -> None:
        self._inner.__exit__(*exc_info)
