#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$PROJECT_DIR"

if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "x86_64" ]]; then
  echo "Ошибка: нативную Intel-сборку нужно выполнять на Intel Mac (x86_64)." >&2
  exit 1
fi

if [[ ! -x "$PROJECT_DIR/.venv/bin/pyinstaller" ]]; then
  "$PROJECT_DIR/install.command"
fi

export PYINSTALLER_CONFIG_DIR="$PROJECT_DIR/.runtime/pyinstaller"
mkdir -p "$PYINSTALLER_CONFIG_DIR"

"$PROJECT_DIR/.venv/bin/python" setup.py build_standalone

mkdir -p "$PROJECT_DIR/dist"
cp "$PROJECT_DIR/LICENSE" "$PROJECT_DIR/NOTICE" "$PROJECT_DIR/dist/"
cp "$PROJECT_DIR/docs/SOURCE_CODE_RU.md" "$PROJECT_DIR/docs/INTEL_MAC_RU.md" \
  "$PROJECT_DIR/docs/FUNCTION_MATRIX_RU.md" "$PROJECT_DIR/docs/TEST_REPORT_RU.md" \
  "$PROJECT_DIR/dist/"

APP_PATH="$PROJECT_DIR/dist/Parser2GIS.app"
if [[ -d "$APP_PATH" ]]; then
  # Build under Documents may be backed by File Provider, which attaches Finder
  # xattrs and invalidates a bundle signature. Stage in /private/tmp, sign there,
  # then publish a clean ZIP (the ZIP itself is unaffected by Finder xattrs).
  STAGE_DIR="$(mktemp -d /private/tmp/parser2gis-package.XXXXXX)"
  trap 'rm -rf "$STAGE_DIR"' EXIT
  /usr/bin/ditto --norsrc --noextattr "$APP_PATH" "$STAGE_DIR/Parser2GIS.app"
  /usr/bin/xattr -cr "$STAGE_DIR/Parser2GIS.app"
  /usr/bin/codesign --force --deep --sign - "$STAGE_DIR/Parser2GIS.app"
  /usr/bin/codesign --verify --deep --strict "$STAGE_DIR/Parser2GIS.app"
  cp "$PROJECT_DIR/LICENSE" "$PROJECT_DIR/NOTICE" "$PROJECT_DIR/docs/SOURCE_CODE_RU.md" \
    "$PROJECT_DIR/docs/INTEL_MAC_RU.md" "$PROJECT_DIR/docs/FUNCTION_MATRIX_RU.md" \
    "$PROJECT_DIR/docs/TEST_REPORT_RU.md" "$STAGE_DIR/"
  (
    cd "$STAGE_DIR"
    /usr/bin/zip -qry -y "$PROJECT_DIR/dist/Parser2GIS-macOS-x86_64.zip" \
      Parser2GIS.app LICENSE NOTICE SOURCE_CODE_RU.md INTEL_MAC_RU.md \
      FUNCTION_MATRIX_RU.md TEST_REPORT_RU.md
  )
  (
    cd "$PROJECT_DIR/dist"
    /usr/bin/shasum -a 256 Parser2GIS-macOS-x86_64.zip \
      > Parser2GIS-macOS-x86_64.zip.sha256
  )
  rm -rf "$STAGE_DIR"
  trap - EXIT
fi

SOURCE_STAGE="$(mktemp -d /private/tmp/parser2gis-source.XXXXXX)"
trap 'rm -rf "$SOURCE_STAGE"' EXIT
mkdir -p "$SOURCE_STAGE/Parser2GIS-source"
/usr/bin/rsync -a \
  --exclude='.git/' --exclude='.venv/' --exclude='.runtime/' --exclude='dist/' \
  --exclude='build/' --exclude='__pycache__/' --exclude='.pytest_cache/' \
  "$PROJECT_DIR/" "$SOURCE_STAGE/Parser2GIS-source/"
(
  cd "$SOURCE_STAGE"
  /usr/bin/zip -qry -y "$PROJECT_DIR/dist/Parser2GIS-source-intel.zip" \
    Parser2GIS-source
)
(
  cd "$PROJECT_DIR/dist"
  /usr/bin/shasum -a 256 Parser2GIS-source-intel.zip \
    > Parser2GIS-source-intel.zip.sha256
)
rm -rf "$SOURCE_STAGE"
trap - EXIT

MAIN_EXECUTABLE="$PROJECT_DIR/dist/Parser2GIS.app/Contents/MacOS/Parser2GIS"
if [[ ! -x "$MAIN_EXECUTABLE" ]] || \
    ! /usr/bin/file "$MAIN_EXECUTABLE" | /usr/bin/grep -q 'Mach-O 64-bit executable x86_64'; then
  echo "Ошибка: главный файл Parser2GIS.app не является Mach-O x86_64." >&2
  exit 1
fi

if [[ "$(/usr/bin/lipo -archs "$MAIN_EXECUTABLE")" != "x86_64" ]]; then
  echo "Ошибка: в Parser2GIS.app найдена архитектура, отличная от x86_64." >&2
  exit 1
fi

FOUND=0
while IFS= read -r candidate; do
  if /usr/bin/file "$candidate" | /usr/bin/grep -q "Mach-O.*x86_64"; then
    echo "Проверено x86_64: $candidate"
    FOUND=1
  fi
done < <(/usr/bin/find "$PROJECT_DIR/dist" -type f -perm -111 -print)

if [[ "$FOUND" -ne 1 ]]; then
  echo "Ошибка: в dist не найден исполняемый Mach-O x86_64." >&2
  exit 1
fi

echo "Сборка завершена: $PROJECT_DIR/dist"
