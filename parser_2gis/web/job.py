from __future__ import annotations

import logging
import threading
from typing import Any, Optional

from ..config import Configuration
from ..logger import logger
from ..parser import get_parser
from ..writer import FilterWriter, get_writer
from ..writer.filters import any_filter_enabled
from ..writer.record import extract_record
from ..writer.writers import FileWriter
from .history import History

# Keep at most this many log lines in memory for the live progress panel.
_MAX_LOG_LINES = 5000


class CollectorWriter(FileWriter):
    """In-memory writer: collects raw catalog documents (no file output).

    Used by the web dashboard so results can be rendered as cards and later
    exported to any format on demand.
    """
    def __init__(self, writer_options) -> None:
        super().__init__('', writer_options)
        self.docs: list[Any] = []

    def __enter__(self) -> 'CollectorWriter':
        return self

    def __exit__(self, *exc_info) -> None:
        pass

    def write(self, catalog_doc: Any) -> None:
        if not self._check_catalog_doc(catalog_doc):
            return
        self.docs.append(catalog_doc)
        if self._options.verbose:
            record = extract_record(catalog_doc)
            logger.info('Парсинг [%d] > %s', len(self.docs),
                        record['name'] if record else '...')


class _ListLogHandler(logging.Handler):
    """Logging handler that appends formatted records to a shared list."""
    def __init__(self, sink: list[str]) -> None:
        super().__init__()
        self._sink = sink
        self.setFormatter(logging.Formatter('%(asctime)s | %(message)s', datefmt='%H:%M:%S'))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._sink.append(self.format(record))
            if len(self._sink) > _MAX_LOG_LINES:
                del self._sink[:len(self._sink) - _MAX_LOG_LINES]
        except Exception:
            pass


class ParseJob:
    """Background parsing job for the web dashboard (single job at a time)."""
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._parser = None
        self._cancelled = False
        self.status = 'idle'  # idle | running | done | stopped | error
        self.logs: list[str] = []
        self.error: Optional[str] = None
        self.collector: Optional[CollectorWriter] = None
        self._urls: list[str] = []
        self._config: Optional[Configuration] = None

    @property
    def running(self) -> bool:
        return self.status == 'running'

    @property
    def resumable(self) -> bool:
        """Whether the last run can be resumed (finished with an error/stop
        and has both collected data and the URLs/config to continue from)."""
        return (self.status in ('error', 'stopped')
                and self.collector is not None
                and bool(self._urls) and self._config is not None)

    @property
    def count(self) -> int:
        return len(self.collector.docs) if self.collector else 0

    def start(self, config: Configuration, urls: list[str]) -> None:
        with self._lock:
            if self.running:
                raise RuntimeError('Парсинг уже запущен')
            self.status = 'running'
            self.logs = []
            self.error = None
            self._cancelled = False
            self.collector = CollectorWriter(config.writer)
            self._urls = urls
            self._config = config

        self._thread = threading.Thread(target=self._run, args=(config, urls), daemon=True)
        self._thread.start()

    def resume(self) -> bool:
        """Continue a run that ended with an error (or was stopped), keeping the
        records already collected. Re-parses the same URLs; dedup skips items that
        were already captured. Returns False if there is nothing to resume."""
        with self._lock:
            if self.running or not self.resumable:
                return False
            config, urls = self._config, self._urls
            assert config is not None
            self.status = 'running'
            self.error = None
            self._cancelled = False

        self._thread = threading.Thread(target=self._run, args=(config, urls),
                                        kwargs={'resume': True}, daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        with self._lock:
            self._cancelled = True
            if self._parser:
                try:
                    self._parser.close()
                except Exception:
                    pass

    def clear(self) -> bool:
        """Drop the current results/logs (history is untouched). No-op while running."""
        with self._lock:
            if self.running:
                return False
            self.collector = None
            self.logs = []
            self.error = None
            self.status = 'idle'
            return True

    def _run(self, config: Configuration, urls: list[str], resume: bool = False) -> None:
        handler = _ListLogHandler(self.logs)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)  # ensure INFO progress lines are captured
        try:
            assert self.collector is not None
            writer: FileWriter = self.collector
            if resume:
                # Force cross-niche dedup so re-scraped, already-collected items
                # are not duplicated when continuing.
                config.filters.dedup_across_niches = True
            if any_filter_enabled(config.filters):
                filter_writer = FilterWriter(self.collector, config.filters)
                if resume:
                    filter_writer.prime(self.collector.docs)
                writer = filter_writer

            if resume:
                logger.info('Парсинг возобновлён. Уже собрано записей: %d.', len(self.collector.docs))
            else:
                logger.info('Парсинг запущен.')
            with writer:
                for url in urls:
                    if self._cancelled:
                        break
                    logger.info('Парсинг ссылки %s', url)
                    try:
                        self._parser = get_parser(url, chrome_options=config.chrome,
                                                  parser_options=config.parser)
                        with self._parser:
                            if not self._cancelled:
                                self._parser.parse(writer)
                    except Exception as e:
                        if self._cancelled:
                            raise  # a stop closed the tab — handled below as clean stop
                        # One URL failing mid-scrape must not abort the rest of the
                        # run — log it and move on to the next link.
                        logger.error('Ссылка прервана из-за ошибки, переход к следующей: %s', e)
                        continue

            self.status = 'stopped' if self._cancelled else 'done'
            logger.info('Парсинг %s.', 'остановлен' if self._cancelled else 'завершён')
        except Exception as e:
            if self._cancelled:
                # Stopping closes the browser tab mid-request, surfacing as
                # "Tab has been stopped" — a clean stop, not a failure.
                self.status = 'stopped'
                logger.info('Парсинг остановлен.')
            else:
                self.error = str(e)
                self.status = 'error'
                logger.error('Ошибка во время работы парсера.', exc_info=True)
        finally:
            self._parser = None
            # Persist whatever was collected — full run, partial stop or error —
            # so the records survive reloads and aren't lost on Stop or a crash.
            if self.status in ('done', 'stopped', 'error') and self.collector and self.collector.docs:
                try:
                    History().save(urls, self.collector.docs,
                                   self.collector._options.model_dump(mode='json'))
                except Exception as e:
                    logger.error('Не удалось сохранить историю: %s', e)
            logger.removeHandler(handler)

    def results(self) -> list[dict]:
        """Presentation-ready records for the dashboard grid."""
        if not self.collector:
            return []
        out = []
        for doc in self.collector.docs:
            record = extract_record(doc)
            if record:
                out.append(record)
        return out

    def export(self, output_path: str, file_format: str) -> None:
        """Write collected documents to `output_path` in the given format."""
        if not self.collector:
            raise RuntimeError('Нет данных для экспорта')
        # Filters were already applied while collecting; export raw collected docs.
        with get_writer(output_path, file_format, self.collector._options) as writer:
            for doc in self.collector.docs:
                writer.write(doc)
