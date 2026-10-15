import csv
import json
import zipfile

import pytest

from parser_2gis.web.server import _build_config, _validated_urls, create_app
from parser_2gis.writer import FilterOptions, WriterOptions, get_writer


def catalog_doc(item_id, name, org_id, contacts, rating=4.8, reviews=25):
    """Small deterministic 2GIS-shaped document used only by tests."""
    return {
        'meta': {'code': 200},
        'result': {'items': [{
            'id': item_id,
            'locale': 'ru_RU',
            'type': 'branch',
            'name_ex': {'primary': name, 'extension': 'тестовая запись'},
            'address_name': 'Тестовая улица, 1',
            'adm_div': [{'name': 'Тестовый город', 'type': 'city'}],
            'org': {'id': org_id, 'name': name, 'branch_count': 2},
            'reviews': {
                'general_rating': rating,
                'general_review_count': reviews,
            },
            'rubrics': [{
                'id': '1', 'kind': 'primary', 'name': 'Тестовая рубрика',
                'short_id': 1,
            }],
            'contact_groups': [{'contacts': contacts}],
        }]},
    }


def test_web_resources_and_generator_are_available():
    app = create_app()
    client = app.test_client()

    index = client.get('/')
    assert index.status_code == 200
    assert b'<html lang="ru">' in index.data
    assert 'Ручная связь через WhatsApp'.encode() in index.data
    assert 'Parser2GIS открыт как файл'.encode() in index.data
    assert b"window.location.protocol==='file:'" in index.data

    generator = client.get('/api/generator')
    assert generator.status_code == 200
    payload = generator.get_json()
    assert payload['countries']
    assert payload['cities']
    assert payload['rubrics']


def test_web_rejects_non_2gis_urls_without_starting_a_job():
    app = create_app()
    client = app.test_client()

    response = client.post('/api/start', json={'urls': ['https://example.com/']})
    assert response.status_code == 400
    assert response.get_json()['ok'] is False
    assert '2gis' in response.get_json()['error']

    response = client.post('/api/start', json={
        'urls': ['https://2gis.ru/moscow'],
    })
    assert response.status_code == 400
    assert response.get_json()['ok'] is False
    assert 'Страницы города' in response.get_json()['error']


def test_url_limits_and_safe_delay_defaults():
    assert _validated_urls([
        'https://2gis.ru/moscow/search/test',
        'https://2gis.ru/moscow/search/test',
    ]) == ['https://2gis.ru/moscow/search/test']

    with pytest.raises(ValueError):
        _validated_urls(['file:///etc/passwd'])
    with pytest.raises(ValueError):
        _validated_urls(['https://2gis.evil.example/search/test'])

    with pytest.raises(ValueError, match='Страницы города'):
        _validated_urls(['https://2gis.ru/moscow'])

    assert _validated_urls([
        'https://2gis.ru/moscow/firm/123',
        'https://2gis.ru/moscow/inside/456',
    ]) == [
        'https://2gis.ru/moscow/firm/123',
        'https://2gis.ru/moscow/inside/456',
    ]

    config = _build_config({
        'max_records': 999999,
        'advanced': {'delay_between_clicks': 0},
    })
    assert config.parser.max_records == 5000
    assert config.parser.delay_between_clicks == 500


def test_api_key_is_kept_in_memory_but_not_serialized():
    config = _build_config({'api_key': 'test-secret-key'})

    assert config.parser.api_key == 'test-secret-key'
    assert 'api_key' not in config.parser.model_dump()
    assert 'test-secret-key' not in config.model_dump_json()


def test_filters_and_all_export_formats(tmp_path):
    phone = {'type': 'phone', 'value': '+7 999 000-00-01', 'text': '+7 999 000-00-01'}
    whatsapp = {
        'type': 'whatsapp', 'value': '+79990000001',
        'url': 'https://wa.me/79990000001?text=hello',
    }
    website = {
        'type': 'website', 'value': 'https://example.test',
        'url': 'https://example.test',
    }
    docs = [
        catalog_doc('100_branch-a', 'Организация один', 'org-1',
                    [phone, whatsapp, website]),
        # Same organization: removed by franchise dedup.
        catalog_doc('101_branch-b', 'Организация один, филиал', 'org-1',
                    [phone, whatsapp, website]),
        # No phone: removed by require_phone.
        catalog_doc('102_branch-c', 'Организация два', 'org-2', [website]),
    ]

    options = WriterOptions(verbose=False)
    options.csv.clean = True
    filters = FilterOptions(
        dedup_franchises=True,
        dedup_across_niches=True,
        require_phone=True,
        min_rating=4.5,
        min_reviews=10,
    )

    outputs = {}
    for fmt in ('csv', 'xlsx', 'json', 'html'):
        path = tmp_path / f'out.{fmt}'
        with get_writer(str(path), fmt, options, filters) as writer:
            for doc in docs:
                writer.write(doc)
        assert path.is_file() and path.stat().st_size > 0
        outputs[fmt] = path

    with outputs['csv'].open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.reader(stream))
    if rows[0][0].startswith('sep='):
        rows = rows[1:]
    assert len(rows) == 2  # header + one filtered record
    assert 'Организация один' in rows[1]

    with outputs['json'].open(encoding='utf-8-sig') as stream:
        assert len(json.load(stream)) == 1

    html = outputs['html'].read_text(encoding='utf-8-sig')
    assert 'Организация один' in html
    assert 'tel:79990000001' in html
    assert 'https://wa.me/79990000001' in html
    assert 'https://2gis.com/firm/100' in html

    assert zipfile.is_zipfile(outputs['xlsx'])
