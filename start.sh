#!/usr/bin/env bash

# shellcheck disable=SC1091

[[ -d "venv" ]] || python3.8 -m venv ./venv
source venv/bin/activate
source .env
export BOT_API_KEY DATABASE_URL FERNET_KEY FROM_EMAIL GROUP_ID LOG_ID SECRET_KEY SENDGRID_API_KEY
pip install -U -r requirements.txt
gunicorn hades:app -b :5500 --workers=8
