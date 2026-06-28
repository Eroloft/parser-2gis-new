from __future__ import annotations

from typing import Any, Optional

from pydantic import ValidationError

from ..logger import logger
from .models import CatalogItem

# Type fallback names for non-firm objects.
TYPE_NAMES = {
    'parking': 'Парковка', 'street': 'Улица', 'road': 'Дорога',
    'crossroad': 'Перекрёсток', 'station': 'Остановка',
}


def extract_record(catalog_doc: Any) -> Optional[dict[str, Any]]:
    """Extract a flat, presentation-ready record from a Catalog Item document.

    Shared by the HTML writer and the web dashboard. Returns `None` for
    malformed documents or entries without a name.
    """
    try:
        item = catalog_doc['result']['items'][0]
    except (KeyError, IndexError, TypeError):
        return None

    try:
        catalog_item = CatalogItem(**item)
    except ValidationError as e:
        logger.error('Ошибка извлечения записи: %s', e.errors()[0].get('loc') if e.errors() else e)
        return None

    # Name / description
    name, description = None, None
    if catalog_item.name_ex:
        name = catalog_item.name_ex.primary
        description = catalog_item.name_ex.extension
    elif catalog_item.name:
        name = catalog_item.name
    elif catalog_item.type in TYPE_NAMES:
        name = TYPE_NAMES[catalog_item.type]
    if not name:
        return None

    city = None
    for div in catalog_item.adm_div:
        if div.type == 'city':
            city = div.name

    rating = review_count = None
    if catalog_item.reviews:
        rating = catalog_item.reviews.general_rating
        review_count = catalog_item.reviews.general_review_count

    # Contacts: keep the first value of each type.
    contacts: dict[str, str] = {}
    for group in catalog_item.contact_groups:
        for contact in group.contacts:
            if contact.type in contacts:
                continue
            if contact.type == 'phone':
                contacts['phone'] = contact.text or contact.value
            elif contact.type == 'email':
                contacts['email'] = contact.value
            elif contact.url:
                contacts[contact.type] = contact.url.split('?')[0]

    return {
        'name': name,
        'description': description,
        'rubrics': [r.name for r in catalog_item.rubrics],
        'address': catalog_item.address_name,
        'city': city,
        'rating': rating,
        'review_count': review_count,
        'contacts': contacts,
        'url': catalog_item.url,
    }
