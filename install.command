#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$PROJECT_DIR"

PYTHON_VERSION="3.12.15"
PYTHON_BUILD_TAG="20261009"
PYTHON_ARCHIVE="cpython-${PYTHON_VERSION}+${PYTHON_BUILD_TAG}-x86_64-apple-darwin-install_only.tar.gz"
PYTHON_URL="https://github.com/astral-sh/python-build-standalone/releases/download/${PYTHON_BUILD_TAG}/${PYTHON_ARCHIVE}"
PYTHON_SHA256="4c84ef5abe4bc145646175fce9b881936d60126b9a3f9a24c6308e2d035ca5c6"
RUNTIME_PYTHON="$PROJECT_DIR/.runtime/python/bin/python3.12"
CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Ошибка: этот установщик предназначен только для macOS." >&2
  exit 1
fi

if [[ "$(uname -m)" != "x86_64" ]]; then
  echo "Ошибка: требуется Intel Mac (x86_64), обнаружено: $(uname -m)." >&2
  exit 1
fi

if [[ ! -x "$CHROME_BIN" ]]; then
  echo "Ошибка: Google Chrome не найден в /Applications." >&2
  echo "Установите Chrome с https://www.google.com/chrome/ и повторите запуск." >&2
  exit 1
fi

if ! /usr/bin/file "$CHROME_BIN" | /usr/bin/grep -q "x86_64"; then
  echo "Ошибка: установленный Google Chrome не содержит архитектуру x86_64." >&2
  exit 1
fi

mkdir -p "$PROJECT_DIR/.runtime"

if [[ ! -x "$RUNTIME_PYTHON" ]]; then
  echo "Загрузка переносимого CPython ${PYTHON_VERSION} для Intel macOS..."
  TEMP_DIR="$(mktemp -d "$PROJECT_DIR/.runtime/python-install.XXXXXX")"
  trap 'rm -rf "$TEMP_DIR"' EXIT
  ARCHIVE_PATH="$TEMP_DIR/$PYTHON_ARCHIVE"
  /usr/bin/curl -fL --retry 3 --connect-timeout 20 "$PYTHON_URL" -o "$ARCHIVE_PATH"
  ACTUAL_SHA256="$(/usr/bin/shasum -a 256 "$ARCHIVE_PATH" | /usr/bin/awk '{print $1}')"
  if [[ "$ACTUAL_SHA256" != "$PYTHON_SHA256" ]]; then
    echo "Ошибка: контрольная сумма CPython не совпала." >&2
    exit 1
  fi
  /usr/bin/tar -xzf "$ARCHIVE_PATH" -C "$TEMP_DIR"
  if [[ -e "$PROJECT_DIR/.runtime/python" ]]; then
    mv "$PROJECT_DIR/.runtime/python" "$PROJECT_DIR/.runtime/python.incomplete.$(date +%Y%m%d%H%M%S)"
  fi
  mv "$TEMP_DIR/python" "$PROJECT_DIR/.runtime/python"
  trap - EXIT
  rm -rf "$TEMP_DIR"
fi

if ! /usr/bin/file -L "$RUNTIME_PYTHON" | /usr/bin/grep -q "x86_64"; then
  echo "Ошибка: переносимый Python не является x86_64." >&2
  exit 1
fi

if [[ ! -x "$PROJECT_DIR/.venv/bin/python" ]]; then
  echo "Создание изолированного окружения .venv..."
  "$RUNTIME_PYTHON" -m venv "$PROJECT_DIR/.venv"
fi

if ! /usr/bin/file -L "$PROJECT_DIR/.venv/bin/python" | /usr/bin/grep -q "x86_64"; then
  echo "Ошибка: существующая .venv создана не для x86_64." >&2
  echo "Переименуйте .venv и повторите запуск install.command." >&2
  exit 1
fi

echo "Установка зависимостей в .venv..."
"$PROJECT_DIR/.venv/bin/python" -m pip install --upgrade pip setuptools wheel
"$PROJECT_DIR/.venv/bin/python" -m pip install -e '.[dev]'

"$PROJECT_DIR/.venv/bin/python" -c "import flask, pydantic, pychrome, psutil, requests, xlsxwriter, parser_2gis; print('Зависимости и Parser2GIS импортируются успешно.')"

echo
echo "Готово: $($PROJECT_DIR/.venv/bin/python --version 2>&1), архитектура x86_64."
echo "Для запуска дважды щёлкните start.command."
