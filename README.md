# QRStuff

This application requires atleast python3.6 to run.

To install all requirements, please run

```bash
pip install -r requirements.txt
```

All the python code in this repository is formatted with [black](https://github.com/psf/black).

A few environment variables should be set for proper functionality

`BOT_API_KEY` - Telegram Bot API Key

`GROUP_ID` - Telegram Group ID

`SENDGRID_API_KEY` - SendGrid API Key

`FROM_EMAIL` - Email address SendGrid should use as sender

`DATABASE_URL` - URL to database including credentials - set by default in heroku

`USERNAME` - Username to access the /users endpoint

`PASSWORD` - Password to access the /users endpoint

To test locally if everything is deployed on heroku

```bash
heroku config -a thescriptgroup --shell > .env
heroku local
```

`heroku local` loads a `.env` file by default. If you do not have access to the project (as external contributors wouldn't), you can simply manually fill in the values in a simple key=value format.

To export everything in .env to your environment, you can simply run
```bash
for f in $(awk -F'=' '{print $1}' .env); do export $f; done
```

There are various ways to run the application

- With gunicorn

```bash
gunicorn tsg_registration:app
```

- Directly running the module

```bash
python3 -m tsg_registration
```
