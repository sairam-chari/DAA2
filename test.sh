#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PYTHON_BIN="${PYTHON_BIN:-python3}"
INPUT_FILE="${1:-}"

if [ -n "$INPUT_FILE" ] && [ -f "$INPUT_FILE" ]; then
    exec "$PYTHON_BIN" "$SCRIPT_DIR/main2.py" < "$INPUT_FILE"
fi

exec "$PYTHON_BIN" "$SCRIPT_DIR/main2.py"
