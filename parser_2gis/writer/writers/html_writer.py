from __future__ import annotations

import html
import re
from typing import Any

from ...logger import logger
from ..record import extract_record
from .file_writer import FileWriter


def _digits(value: str) -> str:
    """Keep digits only (for tel:/wa.me links)."""
    return re.sub(r'\D', '', value or '')


class HTMLWriter(FileWriter):
    """Writer to a self-contained, searchable HTML page.

    Each record is a card with one-click actions: WhatsApp, call, open in 2GIS,
    and social/website/e-mail links. The page works offline (no external assets)
    and has a live client-side search box.
    """
    def __enter__(self) -> 'HTMLWriter':
        super().__enter__()
        self._wrote_count = 0
        self._file.write(_PAGE_HEAD)
        return self

    def __exit__(self, *exc_info) -> None:
        self._file.write(_PAGE_TAIL)
        super().__exit__(*exc_info)

    def write(self, catalog_doc: Any) -> None:
        """Render a Catalog Item API document as a card."""
        if not self._check_catalog_doc(catalog_doc):
            return

        record = extract_record(catalog_doc)
        if not record:
            return

        if self._options.verbose:
            logger.info('Парсинг [%d] > %s', self._wrote_count + 1, record['name'])

        self._file.write(self._render_card(record))
        self._wrote_count += 1

    def _render_card(self, r: dict[str, Any]) -> str:
        c = r['contacts']
        esc = html.escape

        search_blob = ' '.join(filter(None, [
            r['name'], r['address'], r['city'],
            ' '.join(r['rubrics']), c.get('phone', ''),
        ])).lower()

        rating_html = ''
        if r['rating']:
            reviews = f" · {r['review_count']} отз." if r['review_count'] else ''
            rating_html = f'<span class="rating">★ {esc(str(r["rating"]))}{esc(reviews)}</span>'

        rubrics_html = ''
        if r['rubrics']:
            rubrics_html = '<div class="rubrics">' + esc(' · '.join(r['rubrics'])) + '</div>'

        meta_bits = []
        if r['address']:
            meta_bits.append(esc(r['address']))
        if r['city']:
            meta_bits.append(esc(r['city']))
        meta_html = '<div class="meta">' + ', '.join(meta_bits) + '</div>' if meta_bits else ''

        buttons = []
        if 'whatsapp' in c:
            wa = esc(c['whatsapp'])
            buttons.append(f'<a class="btn wa" href="{wa}" target="_blank" rel="noopener">WhatsApp</a>')
        if 'phone' in c:
            buttons.append(f'<a class="btn" href="tel:{_digits(c["phone"])}">📞 {esc(c["phone"])}</a>')
        if 'telegram' in c:
            buttons.append(f'<a class="btn tg" href="{esc(c["telegram"])}" target="_blank" rel="noopener">Telegram</a>')
        if 'instagram' in c:
            buttons.append(f'<a class="btn ig" href="{esc(c["instagram"])}" target="_blank" rel="noopener">Instagram</a>')
        if 'website' in c:
            buttons.append(f'<a class="btn" href="{esc(c["website"])}" target="_blank" rel="noopener">🌐 Сайт</a>')
        if 'email' in c:
            buttons.append(f'<a class="btn" href="mailto:{esc(c["email"])}">✉️ E-mail</a>')
        if r['url']:
            buttons.append(f'<a class="btn gis" href="{esc(r["url"])}" target="_blank" rel="noopener">2GIS</a>')

        return (
            f'<article class="card" data-search="{esc(search_blob)}">'
            f'<div class="card-head"><h2>{esc(r["name"])}</h2>{rating_html}</div>'
            f'{rubrics_html}{meta_html}'
            f'<div class="actions">{"".join(buttons)}</div>'
            f'</article>\n'
        )


_PAGE_HEAD = '''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Результаты 2GIS</title>
<style>
  :root{
    --bg:#f4f5f7; --card:#fff; --text:#1a1d24; --muted:#6b7280; --line:#e6e8ec;
    --accent:#0a84ff; --wa:#25d366; --tg:#229ed9; --ig:#d6307a; --gis:#34c759;
    --shadow:0 1px 2px rgba(16,24,40,.06),0 4px 16px rgba(16,24,40,.06);
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--text);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Inter,Arial,sans-serif;
    -webkit-font-smoothing:antialiased}
  header{position:sticky;top:0;z-index:5;background:rgba(244,245,247,.85);
    backdrop-filter:saturate(180%) blur(12px);border-bottom:1px solid var(--line);
    padding:16px clamp(16px,4vw,40px)}
  .bar{max-width:1200px;margin:0 auto;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
  h1{font-size:20px;margin:0;font-weight:700;letter-spacing:-.01em}
  #count{color:var(--muted);font-size:14px;font-variant-numeric:tabular-nums}
  #q{flex:1;min-width:220px;padding:11px 14px;border:1px solid var(--line);border-radius:12px;
    font-size:15px;background:var(--card);outline:none;transition:border-color .15s,box-shadow .15s}
  #q:focus{border-color:var(--accent);box-shadow:0 0 0 4px rgba(10,132,255,.12)}
  main{max-width:1200px;margin:0 auto;padding:clamp(16px,4vw,40px);
    display:grid;gap:16px;grid-template-columns:repeat(auto-fill,minmax(320px,1fr))}
  .card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px 18px 16px;
    box-shadow:var(--shadow);transition:transform .12s ease,box-shadow .12s ease;
    display:flex;flex-direction:column;gap:8px}
  .card:hover{transform:translateY(-2px);box-shadow:0 6px 24px rgba(16,24,40,.10)}
  .card-head{display:flex;justify-content:space-between;align-items:baseline;gap:10px}
  .card h2{font-size:17px;margin:0;font-weight:650;letter-spacing:-.01em;line-height:1.25}
  .rating{white-space:nowrap;color:#a9700a;background:#fff6e6;border:1px solid #ffe6b0;
    padding:2px 8px;border-radius:999px;font-size:12.5px;font-weight:600}
  .rubrics{color:var(--accent);font-size:13px;font-weight:500}
  .meta{color:var(--muted);font-size:13.5px;line-height:1.4}
  .actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:6px}
  .btn{display:inline-flex;align-items:center;gap:5px;text-decoration:none;font-size:13px;
    font-weight:600;color:var(--text);background:#f1f3f6;border:1px solid var(--line);
    padding:7px 11px;border-radius:10px;transition:filter .12s,transform .06s}
  .btn:hover{filter:brightness(.96)} .btn:active{transform:scale(.97)}
  .btn.wa{background:var(--wa);border-color:transparent;color:#fff}
  .btn.tg{background:#e8f4fb;border-color:#cfe9f8;color:#1b7fb8}
  .btn.ig{background:#fdeef5;border-color:#f7d3e4;color:var(--ig)}
  .btn.gis{background:#eafaef;border-color:#cdeed7;color:#1e9e4a}
  #empty{display:none;text-align:center;color:var(--muted);padding:60px 0;font-size:15px}
  @media (max-width:480px){main{grid-template-columns:1fr}}
</style>
</head>
<body>
<header><div class="bar">
  <h1>Результаты 2GIS</h1>
  <input id="q" type="search" placeholder="Поиск по названию, рубрике, адресу…" autocomplete="off">
  <span id="count"></span>
</div></header>
<main id="list">
'''

_PAGE_TAIL = '''</main>
<div id="empty">Ничего не найдено</div>
<script>
(function(){
  var list=document.getElementById('list');
  var cards=[].slice.call(list.querySelectorAll('.card'));
  var q=document.getElementById('q');
  var count=document.getElementById('count');
  var empty=document.getElementById('empty');
  function plural(n){var a=n%10,b=n%100;
    if(a===1&&b!==11)return 'заведение';
    if(a>=2&&a<=4&&(b<10||b>=20))return 'заведения';return 'заведений';}
  function update(){
    var term=q.value.trim().toLowerCase();
    var shown=0;
    for(var i=0;i<cards.length;i++){
      var ok=!term||cards[i].getAttribute('data-search').indexOf(term)>-1;
      cards[i].style.display=ok?'':'none';
      if(ok)shown++;
    }
    count.textContent=shown+' '+plural(shown);
    empty.style.display=shown?'none':'block';
  }
  q.addEventListener('input',update);
  update();
})();
</script>
</body>
</html>
'''
