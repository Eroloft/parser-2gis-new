# Обогащение лидов (enricher)

После парсинга 2GIS можно включить пост-обработку:

1. **Контакты** — нормализация телефонов (+7…), вытаскивание Telegram (`@` / t.me), VK, WhatsApp, Instagram, e-mail, сайта из полей 2GIS и из текста.
2. **Сайт** — HTTP(S) доступность, редирект, HTTPS/SSL, эвристический **score современности** (`modern` / `average` / `outdated` / `dead`) по viewport, SPA-фреймворкам, CDN, старому jQuery и т.п.
3. **Дедуп** — по id, `название+адрес`, `название+телефон`; опционально история прошлых запусков (jsonl), чтобы не показывать уже собранные заведения.

## Включение

В коде / конфиге writer:

```python
from parser_2gis.writer.options import WriterOptions, EnrichWriterOptions

opts = WriterOptions(
    enrich=EnrichWriterOptions(
        enabled=True,
        check_websites=True,
        max_workers=8,
        dedup_name_address=True,
        dedup_name_phone=True,
        # dedup_history_path='.parser2gis_history.jsonl',
        # skip_seen_in_history=True,
    )
)
```

CLI (после подключения флагов в `main`/`cli`):

```bash
parser-2gis-new -i URL -o out.xlsx -f xlsx --writer.enrich.enabled true
```

Программный пайплайн:

```python
from parser_2gis.enricher.pipeline import run_enrichment
from parser_2gis.writer.options import EnrichWriterOptions
from parser_2gis.writer.record import extract_record

flats = [extract_record(doc) for doc in docs if extract_record(doc)]
table = run_enrichment(flats, EnrichWriterOptions(enabled=True, check_websites=True))
```

## Колонки в таблице

Дополнительно к стандартным: `phone`, `email`, `website`, `telegram`, `telegram_url`, `vkontakte`, `whatsapp`, `instagram`, `facebook`, `site_ok`, `site_status`, `site_https`, `site_modernity`, `site_modernity_score`, `site_title`, `site_error`.

## Зависимости

Только stdlib (urllib, ssl, concurrent.futures). Опционально позже: `httpx` для пула соединений.

## Идеи на будущее (решай сам)

- Проверка MX для e-mail
- Валидация WhatsApp-ссылки (без API — только формат)
- Поиск Telegram/VK по названию через публичный поиск (осторожно с ToS)
- Скор «качества лида» (есть телефон + живой сайт + TG)
- Экспорт сразу в Google Sheets / CRM webhook
- Кэш проверок сайтов (sqlite) между запусками
