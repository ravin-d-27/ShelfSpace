# build_files.sh
set -e

PYTHON_BIN=python3.9
if ! command -v "$PYTHON_BIN" > /dev/null 2>&1; then
  PYTHON_BIN=python3
fi

rm -rf .venv
"$PYTHON_BIN" -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py collectstatic --noinput
