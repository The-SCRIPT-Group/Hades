#!/usr/bin/env bash

# shellcheck disable=SC1091

[[ -d "venv" ]] || python3.8 -m venv ./venv
source venv/bin/activate
pip install -U -r requirements.txt
gunicorn hades:app -b :5500 --workers=8
