from __future__ import annotations

import csv
import os
import shutil
import tempfile
from typing import Any

from xlsxwriter.workbook import Workbook

from .csv_writer import CSVWriter

# Header substring whose cells hold e-mails (turned into mailto: links).
_EMAIL_HEADER = 'E-mail'
# Max column width (characters) so long URLs don't blow up the layout.
_MAX_COL_WIDTH = 60
# Characters Excel forbids in worksheet names.
_INVALID_SHEET_CHARS = '[]:*?/\\'


class XLSXWriter(CSVWriter):
    """Writer (post-process converter) to XLSX table.

    Produces a polished spreadsheet: bold frozen header, auto-fitted column
    widths, an autofilter, and clickable links (URLs, `tel:` phones, `mailto:`
    e-mails).
    """
    def __exit__(self, *exc_info) -> None:
        super().__exit__(*exc_info)

        with self._open_file(self._file_path, 'r') as f_csv:
            rows = list(csv.reader(f_csv))

        # Drop the Excel `sep=,` hint line added by CSVWriter (not a data row here).
        if rows and rows[0] and rows[0][0].startswith('sep='):
            rows = rows[1:]

        if not rows:
            return

        tmp_xlsx_name = os.path.splitext(self._file_path)[0] + '.converted.xlsx'
        with Workbook(tmp_xlsx_name, {'strings_to_urls': False}) as workbook:
            _render_sheet(workbook, workbook.add_worksheet(), rows)

        shutil.move(tmp_xlsx_name, self._file_path)

    @staticmethod
    def _write_cell(worksheet, r: int, c: int, header: str, value: str, link_fmt) -> None:
        """Write a single cell, turning web URLs / e-mails into clickable links.

        Phones are kept as plain text (xlsxwriter does not support `tel:` links).
        Unsupported or over-long URLs fall back to plain text.
        """
        if not value:
            return

        try:
            if value.startswith(('http://', 'https://')):
                worksheet.write_url(r, c, value, link_fmt, string=value)
                return
            if _EMAIL_HEADER in header and '@' in value:
                worksheet.write_url(r, c, 'mailto:%s' % value, link_fmt, string=value)
                return
        except Exception:
            pass  # Unsupported / over-long URL — fall back to plain text

        worksheet.write(r, c, value)


def _render_sheet(workbook, worksheet, rows: list[list[str]]) -> None:
    """Render CSV `rows` (header + body) onto `worksheet` with the standard style."""
    if not rows:
        return

    header = rows[0]
    body = rows[1:]
    col_widths = [len(h) for h in header]

    header_fmt = workbook.add_format({'bold': True, 'bg_color': '#F2F2F2',
                                      'border': 1, 'border_color': '#D9D9D9'})
    link_fmt = workbook.add_format({'font_color': '#0563C1', 'underline': 1})

    # Header
    for c, title in enumerate(header):
        worksheet.write(0, c, title, header_fmt)

    # Body
    for r, row in enumerate(body, start=1):
        for c, value in enumerate(row):
            if c < len(col_widths):
                col_widths[c] = max(col_widths[c], len(value))
            XLSXWriter._write_cell(worksheet, r, c, header[c] if c < len(header) else '',
                                   value, link_fmt)

    # Auto column widths
    for c, width in enumerate(col_widths):
        worksheet.set_column(c, c, min(width + 2, _MAX_COL_WIDTH))

    # Freeze header + autofilter
    worksheet.freeze_panes(1, 0)
    if header:
        worksheet.autofilter(0, 0, max(len(body), 1), len(header) - 1)


def _safe_sheet_name(name: str, used: set) -> str:
    """Sanitize a district label into a unique, Excel-legal worksheet name."""
    name = (name or 'Лист').strip()
    for ch in _INVALID_SHEET_CHARS:
        name = name.replace(ch, ' ')
    name = name.strip()[:31] or 'Лист'
    base, i = name, 2
    while name.lower() in used:
        suffix = ' %d' % i
        name = base[:31 - len(suffix)] + suffix
        i += 1
    used.add(name.lower())
    return name


def _docs_to_rows(docs: list[Any], writer_options) -> list[list[str]]:
    """Convert catalog documents to CSV rows via a throwaway CSVWriter.

    Reuses the CSV writer so the clean-view preset, empty-column and duplicate
    removal all apply identically to each sheet.
    """
    fd, tmp = tempfile.mkstemp(suffix='.csv')
    os.close(fd)
    try:
        with CSVWriter(tmp, writer_options) as w:
            for doc in docs:
                w.write(doc)
        with open(tmp, 'r', encoding=writer_options.encoding, newline='', errors='replace') as f:
            rows = list(csv.reader(f))
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass

    if rows and rows[0] and rows[0][0].startswith('sep='):
        rows = rows[1:]
    return rows


def write_multisheet_xlsx(file_path: str, groups: list[tuple[str, list[Any]]],
                          writer_options) -> None:
    """Write an XLSX with one worksheet per (sheet_name, docs) group.

    Used by the web dashboard to split district-scoped results onto separate
    sheets. Falls back to a single blank sheet if every group is empty.
    """
    tmp_xlsx = os.path.splitext(file_path)[0] + '.converted.xlsx'
    used: set[str] = set()
    with Workbook(tmp_xlsx, {'strings_to_urls': False}) as workbook:
        wrote_any = False
        for name, docs in groups:
            rows = _docs_to_rows(docs, writer_options)
            if not rows:
                continue
            _render_sheet(workbook, workbook.add_worksheet(_safe_sheet_name(name, used)), rows)
            wrote_any = True
        if not wrote_any:
            workbook.add_worksheet()  # Excel requires at least one worksheet
    shutil.move(tmp_xlsx, file_path)
