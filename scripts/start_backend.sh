#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname -- "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

if [[ -x "$PROJECT_ROOT/.venv/bin/python" ]]; then
    PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
else
    PYTHON_BIN="${PYTHON_BIN:-python3}"
fi

exec "$PYTHON_BIN" -m uvicorn backend.app.main:app \
    --host "${BACKEND_HOST:-127.0.0.1}" \
    --port "${BACKEND_PORT:-8000}" \
    --reload
