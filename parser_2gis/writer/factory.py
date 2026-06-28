from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .writers import CSVWriter, XLSXWriter, FileWriter, JSONWriter, HTMLWriter

from .exceptions import WriterUnknownFileFormat
from .filters import FilterWriter, any_filter_enabled

if TYPE_CHECKING:
    from .options import FilterOptions, WriterOptions


def get_writer(file_path: str, file_format: str, writer_options: WriterOptions,
               filter_options: Optional[FilterOptions] = None) -> FileWriter:
    """Writer factory function.

    Args:
        output_path: Path to thr result file.
        format: `csv`, `xlsx` or `json` format.
        writer_options: Writer options.
        filter_options: Record-level filters. If any filter is active, the
            returned writer is wrapped in a `FilterWriter`.

    Returns:
        File Writer instance.
    """
    if file_format == 'json':
        writer: FileWriter = JSONWriter(file_path, writer_options)
    elif file_format == 'csv':
        writer = CSVWriter(file_path, writer_options)
    elif file_format == 'xlsx':
        writer = XLSXWriter(file_path, writer_options)
    elif file_format == 'html':
        writer = HTMLWriter(file_path, writer_options)
    else:
        raise WriterUnknownFileFormat('Неизвестный формат файла: %s', file_format)

    if filter_options is not None and any_filter_enabled(filter_options):
        return FilterWriter(writer, filter_options)

    return writer
