# QRStuff

This application python3.6 atleast

To install all requirements, please run

```bash
pip install -r requirements.txt
```

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
heroku config -a the-script-group --shell > .env
heroku local
```

To export everything in .env
```bash
for f in $(awk -F'=' '{print $1}' .env); do export $f; done
```


There are various ways to run it

```bash
gunicorn tsg_registration:app
```
or
```bash
python3 -m tsg_registration
```