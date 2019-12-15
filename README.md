# Hades - TSG Event Management Application

This application requires atleast python3.6 to run.

To install all requirements, please run

```bash
pip install -r requirements.txt
```

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A few environment variables should be set for proper functionality

`BOT_API_KEY` - Telegram Bot API Key

`GROUP_ID` - Telegram Group ID

`LOG_ID` - Telegram Channel ID (for logging purposes)

`SENDGRID_API_KEY` - SendGrid API Key

`FROM_EMAIL` - Email address SendGrid should use as sender

`DATABASE_URL` - URL to database including credentials - set by default in heroku

To test locally if everything is deployed on heroku

To export everything in .env to your environment, you can simply run
```bash
for f in $(awk -F'=' '{print $1}' .env); do export $f; done
```

There are various ways to run the application

- With gunicorn

```bash
gunicorn hades:app
```

- Directly running the module

```bash
python3 -m hades
```
