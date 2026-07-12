#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"

VENV_DIR=".venv"
PYTHON="$VENV_DIR/bin/python"

if [ ! -x "$PYTHON" ]; then
  python3 -m venv "$VENV_DIR"
fi

"$PYTHON" -m pip install --upgrade pip
"$PYTHON" -m pip install --upgrade -r requirements.txt

exec "$PYTHON" -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload --reload-dir app --timeout-graceful-shutdown 1
