#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$PROJECT_DIR"

if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "x86_64" ]]; then
  echo "Ошибка: start.command предназначен для Intel Mac (x86_64)." >&2
  exit 1
fi

if [[ ! -x "$PROJECT_DIR/.venv/bin/python" ]]; then
  echo "Первый запуск: сначала будет создана локальная .venv."
  "$PROJECT_DIR/install.command"
fi

if [[ ! -f "$PROJECT_DIR/parser-2gis.py" || ! -f "$PROJECT_DIR/parser_2gis/__init__.py" ]]; then
  echo "Ошибка: исходные файлы Parser2GIS повреждены или отсутствуют." >&2
  exit 1
fi

if ! "$PROJECT_DIR/.venv/bin/python" -c \
  'import flask, pydantic, pychrome, psutil, requests, xlsxwriter' >/dev/null 2>&1; then
  echo "Локальное окружение неполное. Восстанавливаю зависимости..."
  "$PROJECT_DIR/install.command"
fi

WEB_PORT="8666"
PREVIOUS_ARG=""
for ARG in "$@"; do
  if [[ "$PREVIOUS_ARG" == "--web-port" ]]; then
    WEB_PORT="$ARG"
    break
  fi
  case "$ARG" in
    --web-port=*) WEB_PORT="${ARG#*=}"; break ;;
  esac
  PREVIOUS_ARG="$ARG"
done

echo "Запуск Parser2GIS: http://127.0.0.1:${WEB_PORT}/"
echo "Для завершения нажмите Ctrl+C или закройте это окно терминала."

# Запускаем исходный модуль напрямую. Это не зависит от editable-entry-point,
# который на некоторых macOS/File Provider томах может временно не увидеть пакет.
export PYTHONPATH="$PROJECT_DIR${PYTHONPATH:+:$PYTHONPATH}"
exec "$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/parser-2gis.py" --web "$@"
