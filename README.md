# Hades - TSG Event Management Application

This application requires atleast python3.6 to run.

To install all requirements, please run

```bash
pip install -r requirements.txt
```

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A few environment variables should be set for proper functionality -- you can just add these in a `.env` file and `decouple` will pick them up

`BOT_API_KEY` - Telegram Bot API Key

`GROUP_ID` - Telegram Group ID

`LOG_ID` - Telegram Channel ID (for logging purposes)

`SENDGRID_API_KEY` - SendGrid API Key

`FROM_EMAIL` - Email address SendGrid should use as sender

`DATABASE_URL` - URL to MySQL (can change, but need to update requirements accordingly) database including credentials

`FERNET_KEY` - Key for Fernet cryptography algorithm


There are various ways to run the application

- With gunicorn

```bash
gunicorn hades:app
```

- Directly running the module

```bash
python3 -m hades
```
