#!/usr/bin/env bash

# shellcheck disable=SC1091

[[ -d "venv" ]] || python3.8 -m venv ./venv
source venv/bin/activate
source .env
export AUTHORIZATION_TOKEN BOT_API_KEY DATABASE_URL FROM_EMAIL GROUP_ID NOTIFY_ID SECRET_KEY SENDGRID_API_KEY
pip install -r requirements.txt
gunicorn hades:app -b :5500
