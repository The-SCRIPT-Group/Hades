#!/usr/bin/env python3
"""
Flask application to accept some details, generate, display, and email a QR code to users
"""

# pylint: disable=invalid-name,too-few-public-methods,no-member,line-too-long,too-many-locals

import base64
import os
from datetime import datetime

import qrcode
from flask import Flask, redirect, render_template, request, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Attachment, Content, Mail
from sqlalchemy import asc, desc, exc
from telegram import ChatAction
from telegram.ext import Updater

updater = Updater(os.getenv("BOT_API_KEY"))

FROM_EMAIL = os.getenv("FROM_EMAIL")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

app = Flask(__name__)
db = SQLAlchemy(app)

from tsg_registration.utils import users_to_json

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")

DEPARTMENTS = {
    "cse": "Computer Science and Engineering",
    "ece": "Electronics and Communication Engineering",
    "ee": "Electrical Engineering",
    "mech": "Mechanical Engineering",
    "r&a": "Robotics and Automation",
    "civil": "Civil Engineering",
    "chem": "Chemical Engineering",
    "polymer": "Polymer Engineering",
    "petroleum": "Petroleum Engineering",
    "others": "Others",
}

BLACKLISTED_FIELDS = (
    "chat_id",
    "date",
    "db",
    "email_second_person",
    "event",
    "extra_field_telegram",
    "extra_message",
    "name_second_person",
    "whatsapp_number",
)

EVENTS = {
    "codex_april_2019": "CodeX April 2019",
    "eh_july_2019": "Ethical Hacking July 2019",
    "cpp_workshop_may_2019": "CPP Workshop May 2019",
    "rsc_2019": "RSC 2019",
    "c_cpp_workshop_august_2019": "C/C++ August 2019",
    "do_hacktoberfest_2019": "DigitalOcean Hacktoberfest 2019",
    "csi_november_2019": "CSI November 2019",
}

EVENT_EXTRA_INFO = {"csi_november_2019": {"PRN": "prn", "CSI ID": "csi_id"}}


from tsg_registration.models.csi import CSINovember2019
from tsg_registration.models.codex import CodexApril2019, RSC2019
from tsg_registration.models.techo import EHJuly2019
from tsg_registration.models.workshop import (
    CPPWSMay2019,
    CCPPWSAugust2019,
    Hacktoberfest2019,
)

EVENT_CLASSES = {
    "codex_april_2019": CodexApril2019,
    "eh_july_2019": EHJuly2019,
    "cpp_workshop_may_2019": CPPWSMay2019,
    "rsc_2019": RSC2019,
    "c_cpp_workshop_august_2019": CCPPWSAugust2019,
    "do_hacktoberfest_2019": Hacktoberfest2019,
    "csi_november_2019": CSINovember2019,
}


def get_db_by_name(name: str) -> db.Model:
    """Returns the database model class corresponding to the given name."""
    try:
        return EVENT_CLASSES[name]
    except KeyError:
        return None


@app.route("/submit", methods=["POST"])
def submit():
    """Take data from the form, generate, display, and email QR code to user."""
    table = get_db_by_name(request.form["db"])

    if table is None:
        print(request.form["db"])
        return "Error occurred. Kindly contact someone from the team and we will have this resolved ASAP"

    event_name = request.form["event"]

    id = get_current_id(table)

    data = {}

    for k, v in request.form.items():
        if k in BLACKLISTED_FIELDS:
            continue
        data[k] = v

    user = table(**data, id=id)

    if request.form["whatsapp_number"]:
        user.phone += f"|{request.form['whatsapp_number']}"

    data = user.validate()
    if data is not True:
        return data

    img = generate_qr(user)
    img.save("qr.png")
    img_data = open("qr.png", "rb").read()
    encoded = base64.b64encode(img_data).decode()

    try:
        db.session.add(user)
        db.session.commit()
    except exc.IntegrityError as e:
        print(e)
        return """It appears there was an error while trying to enter your data into our database.<br/>Kindly contact someone from the team and we will have this resolved ASAP"""

    name = user.name
    from_email = FROM_EMAIL
    to_emails = []
    email_1 = (user.email, name)
    to_emails.append(email_1)
    if "email_second_person" in request.form and "name_second_person" in request.form:
        email_2 = (
            request.form["email_second_person"],
            request.form["name_second_person"],
        )
        name += ", {}".format(request.form["name_second_person"])
        to_emails.append(email_2)

    try:
        date = request.form["date"]
    except KeyError:
        date = datetime.now().strftime("%B,%Y")
    subject = "Registration for {} - {} - ID {}".format(event_name, date, id)
    message = """<img src='https://drive.google.com/uc?id=12VCUzNvU53f_mR7Hbumrc6N66rCQO5r-&export=download' style="width:30%;height:50%">
<hr>
{}, your registration is done!
<br/>
A QR code has been attached below!
<br/>
You're <b>required</b> to present this on the day of the event.""".format(
        name
    )
    try:
        message += "<br/>" + request.form["extra_message"]
    except KeyError:
        pass
    content = Content("text/html", message)
    mail = Mail(from_email, to_emails, subject, html_content=content)
    mail.add_attachment(Attachment(encoded, "qr.png", "image/png"))

    try:
        response = SendGridAPIClient(SENDGRID_API_KEY).send(mail)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e)

    chat_id = (
        request.form["chat_id"] if "chat_id" in request.form else os.getenv("GROUP_ID")
    )
    caption = f"Name: {user.name} | ID: {user.id}"
    if "extra_field_telegram" in request.form:
        caption += f" | {request.form['extra_field_telegram']} - {request.form[request.form['extra_field_telegram']]}"
    updater.bot.sendChatAction(chat_id, action=ChatAction.TYPING)
    updater.bot.sendMessage(chat_id, f"New registration for {event_name}!")
    updater.bot.sendDocument(chat_id, document=open("qr.png", "rb"), caption=caption)

    return 'Please save this QR Code. It has also been emailed to you.<br><img src=\
            "data:image/png;base64, {}"/>'.format(
        encoded
    )


@app.route("/login/<user>", methods=["GET", "POST"])
def login(user):
    """Display the list of users in the desired database, after authentication."""
    if request.method == "POST":
        prefix = "CSI_" if user == "csi" else ""
        password = request.form["password"]
        if password == os.getenv(f"{prefix}PASSWORD"):
            table = get_db_by_name(request.form["table"])
            if table is None:
                return f"Error while choosing table {request.form['table']}!"
            user_data = db.session.query(table).order_by(asc(table.id))
            if user_data:
                try:
                    extra_columns = EVENT_EXTRA_INFO[request.form["table"]]
                except KeyError:
                    extra_columns = {}
                return render_template(
                    "users.html", users=user_data, extra_columns=extra_columns
                )
            return f"No users found in table {request.form['table']}"
        return "Invalid password!"
    if user == "tsg":
        return render_template("login.html", events=EVENTS, user=user)
    elif user == "csi":
        return render_template(
            "login.html", events={"csi_november_2019": "CSI November 2019"}, user=user
        )
    return f"Hi {user}, what exactly are you trying to do?"


@app.route("/users")
def users():
    """Just redirects to the new /login/tsg route"""
    return redirect(url_for("login", user="tsg"))


@app.route("/api/events")
def events_api():
    """Returns a JSON consisting of the tables the user has the permission to view"""
    authorization_token = request.headers.get("Authorization")
    if authorization_token == os.getenv("AUTHORIZATION_TOKEN"):
        ret = (jsonify({"response": list(EVENTS.keys())}), 200)
    elif authorization_token == os.getenv("CSI_AUTHORIZATION_TOKEN"):
        ret = (jsonify({"response": ("csi_november_2019",)}), 200)
    else:
        ret = (jsonify({"message": "Unauthorized"}), 401)
    return ret


@app.route("/api/users")
def users_api():
    """Returns a JSON consisting of the users in the given table"""
    authorization_token = request.headers.get("Authorization")
    if authorization_token == os.getenv("AUTHORIZATION_TOKEN"):
        table = get_db_by_name(request.args.get("table"))
        ret = (users_to_json(db.session.query(table).order_by(asc(table.id))), 200)
    elif authorization_token == os.getenv("CSI_AUTHORIZATION_TOKEN"):
        table = CSINovember2019
        ret = (users_to_json(db.session.query(table).order_by(asc(table.id))), 200)
    else:
        ret = (jsonify({"message": "Unauthorized"}), 401)
    return ret


@app.route("/csi")
def csi():
    return render_template(
        "csi.html",
        event="CSI Technovision",
        date="9th November 2019",
        db="csi_november_2019",
        year=True,
        chat_id="-390535990",
    )


@app.route("/")
def root():
    """Root endpoint. Displays the form to the user."""
    return "<marquee>Nothing here right now!</marquee>"


def get_current_id(table: db.Model):
    """Function to return the latest ID based on the database entries. 1 if DB is empty."""
    try:
        id = db.session.query(table).order_by(desc(table.id)).first().id
    except Exception:
        id = 0
    return int(id) + 1


def generate_qr(user):
    """Function to generate and return a QR code based on the given data."""
    data = ""
    for k, v in user.__dict__.items():
        if k == "_sa_instance_state":
            continue
        data += f"{v}|"
    return qrcode.make(data[:-1])
