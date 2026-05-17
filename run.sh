#!/usr/bin/env bash
# Launch the Merisio GUI from a source checkout.
# On first run, creates a local .venv and installs dependencies.
# Subsequent runs reuse the existing .venv.
set -e

cd "$(dirname "$0")"

if [ ! -d .venv ]; then
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
fi

exec .venv/bin/python main.py "$@"
