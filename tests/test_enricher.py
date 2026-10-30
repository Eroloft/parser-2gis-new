"""Unit tests for enricher (no network required for contact/dedup)."""

from __future__ import annotations

from parser_2gis.enricher import ContactFinder, Deduplicator, DedupOptions
from parser_2gis.enricher.contacts import _clean_phone


def test_clean_phone_ru():
    assert _clean_phone('8 (999) 123-45-67') == '+79991234567'
    assert _clean_phone('+7 999 123 45 67') == '+79991234567'
    assert _clean_phone('79991234567') == '+79991234567'


def test_contacts_from_2gis():
    finder = ContactFinder()
    nc = finder.from_2gis_contacts({
        'phone': '+7 999 111-22-33',
        'email': 'shop@example.com',
        'website': 'https://example.com/',
        'telegram': 'https://t.me/myshop',
        'vkontakte': 'https://vk.com/myshop',
        'whatsapp': 'https://wa.me/79991112233',
    })
    assert nc.primary_phone() == '+79991112233'
    assert nc.primary_email() == 'shop@example.com'
    assert nc.website == 'https://example.com'
    assert nc.telegram == '@myshop'
    assert nc.telegram_url == 'https://t.me/myshop'
    assert 'vk.com/myshop' in (nc.vkontakte or '')
    assert nc.whatsapp == '+79991112233'


def test_contacts_from_text():
    finder = ContactFinder()
    nc = finder.from_text(
        'Пишите в Telegram @coolcafe или vk.com/coolcafe, тел 8-900-111-22-33'
    )
    assert nc.telegram == '@coolcafe'
    assert nc.vkontakte and 'coolcafe' in nc.vkontakte
    assert nc.primary_phone() == '+79001112233'


def test_dedup_name_address():
    dedup = Deduplicator(DedupOptions(by_id=False, by_name_address=True, by_name_phone=False))
    a = {'name': 'Кафе Ромашка', 'address': 'ул. Ленина, 1'}
    b = {'name': 'Кафе Ромашка', 'address': 'улица Ленина д.1'}
    c = {'name': 'Другое', 'address': 'ул. Ленина, 1'}
    assert not dedup.is_duplicate(a)
    assert dedup.is_duplicate(b)
    assert not dedup.is_duplicate(c)


def test_dedup_filter():
    dedup = Deduplicator(DedupOptions())
    records = [
        {'name': 'A', 'address': 'x', 'phone': '+79991112233', 'id': '1'},
        {'name': 'A', 'address': 'x', 'phone': '+79991112233', 'id': '1'},
        {'name': 'B', 'address': 'y', 'phone': '+79994445566', 'id': '2'},
    ]
    out = dedup.filter(records)
    assert len(out) == 2
