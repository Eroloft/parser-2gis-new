from __future__ import annotations

import csv
import os
import shutil

from xlsxwriter.workbook import Workbook

from .csv_writer import CSVWriter

# Header substring whose cells hold e-mails (turned into mailto: links).
_EMAIL_HEADER = 'E-mail'
# Max column width (characters) so long URLs don't blow up the layout.
_MAX_COL_WIDTH = 60


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

        if not rows:
            return

        header = rows[0]
        body = rows[1:]
        col_widths = [len(h) for h in header]

        tmp_xlsx_name = os.path.splitext(self._file_path)[0] + '.converted.xlsx'
        with Workbook(tmp_xlsx_name, {'strings_to_urls': False}) as workbook:
            header_fmt = workbook.add_format({'bold': True, 'bg_color': '#F2F2F2',
                                              'border': 1, 'border_color': '#D9D9D9'})
            link_fmt = workbook.add_format({'font_color': '#0563C1', 'underline': 1})
            worksheet = workbook.add_worksheet()

            # Header
            for c, title in enumerate(header):
                worksheet.write(0, c, title, header_fmt)

            # Body
            for r, row in enumerate(body, start=1):
                for c, value in enumerate(row):
                    if c < len(col_widths):
                        col_widths[c] = max(col_widths[c], len(value))
                    self._write_cell(worksheet, r, c, header[c] if c < len(header) else '',
                                     value, link_fmt)

            # Auto column widths
            for c, width in enumerate(col_widths):
                worksheet.set_column(c, c, min(width + 2, _MAX_COL_WIDTH))

            # Freeze header + autofilter
            worksheet.freeze_panes(1, 0)
            if header:
                worksheet.autofilter(0, 0, max(len(body), 1), len(header) - 1)

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
