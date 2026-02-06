#!/bin/bash
# Setup Graphene v2 environment (separate venv)

set -e

cd "$(dirname "$0")/.."

VENV_DIR=".venv-graphene-v2"
REQUIREMENTS_FILE="requirements-graphene-v2.txt"

# Graphene-Django v2 requires Django 3.2, which is only supported on Python 3.10 and lower.
PYTHON_BIN="${PYTHON_BIN:-}"
if [ -z "$PYTHON_BIN" ]; then
    if command -v python3.10 >/dev/null 2>&1; then
        PYTHON_BIN="python3.10"
    elif command -v python3.9 >/dev/null 2>&1; then
        PYTHON_BIN="python3.9"
    elif command -v python3.8 >/dev/null 2>&1; then
        PYTHON_BIN="python3.8"
    else
        PYTHON_BIN="python3"
    fi
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Graphene v2 venv at $VENV_DIR using $PYTHON_BIN..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
else
    echo "Graphene v2 venv already exists at $VENV_DIR"
fi

PY="$VENV_DIR/bin/python"

if [ ! -x "$PY" ]; then
    echo "ERROR: venv python not found at $PY"
    exit 1
fi

VENV_PY_VERSION="$("$PY" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
case "$VENV_PY_VERSION" in
    3.8|3.9|3.10) ;;
    *)
        echo "ERROR: Graphene v2 requires Python 3.10 or lower. Found $VENV_PY_VERSION in $VENV_DIR."
        echo "Delete $VENV_DIR and rerun: ./setup_graphene_v2.sh"
        exit 1
        ;;
esac

"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r "$REQUIREMENTS_FILE"

# Run Django migrations using the v2 environment
"$PY" manage.py migrate --run-syncdb --settings=django_project.settings_graphene_v2

# Seed Django database with 10 users (if needed)
"$PY" - <<'PYCODE'
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'django_project.settings_graphene_v2'

import django
django.setup()

from django_project.users.models import BenchmarkUser

if BenchmarkUser.objects.count() < 10:
    users = [
        BenchmarkUser(
            username=f'user{i:02d}',
            email=f'user{i:02d}@example.com',
            first_name=f'First{i}',
            last_name=f'Last{i}',
        )
        for i in range(10)
    ]
    BenchmarkUser.objects.bulk_create(users, ignore_conflicts=True)
    print(f'Created {len(users)} users')
else:
    print(f'Already have {BenchmarkUser.objects.count()} users')
PYCODE

echo "Graphene v2 environment ready."
