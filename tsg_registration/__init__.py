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

from tsg_registration.models.csi import CSINovember2019
from tsg_registration.models.codex import CodexApril2019, RSC2019
from tsg_registration.models.techo import EHJuly2019
from tsg_registration.models.workshop import (
    CPPWSMay2019,
    CCPPWSAugust2019,
    Hacktoberfest2019,
)


def get_db_by_name(name: str) -> db.Model:
    """Returns the database model class corresponding to the given name."""
    if name == "codex_april_2019":
        return CodexApril2019
    if name == "cpp_workshop_may_2019":
        return CPPWSMay2019
    if name == "eh_july_2019":
        return EHJuly2019
    if name == "c_cpp_workshop_august_2019":
        return CCPPWSAugust2019
    if name == "rsc_2019":
        return RSC2019
    return Hacktoberfest2019


@app.route("/submit", methods=["POST"])
def submit():
    """Take data from the form, generate, display, and email QR code to user."""
    table = get_db_by_name(request.form["db"])
    event_name = request.form["event"]

    id = get_current_id(table)

    user = table(
        name=request.form["name"],
        email=request.form["email"],
        phone=request.form["phone_number"],
        id=id,
    )

    if "department" in request.form:
        user.department = request.form["department"]

    if "year" in request.form:
        user.year = request.form["year"]

    if request.form["whatsapp_number"]:
        user.phone += f"|{request.form['whatsapp_number']}"

    if request.form["miscellaneous"]:
        user.miscellaneous = request.form["miscellaneous"]

    data = user.validate()
    if data is not True:
        return data

    try:
        db.session.add(user)
        db.session.commit()
    except exc.IntegrityError as e:
        print(e)
        return """It appears there was an error while trying to enter your data into our database.<br/>Kindly contact someone from the team and we will have this resolved ASAP"""

    img = generate_qr(request.form, id)
    img.save("qr.png")
    img_data = open("qr.png", "rb").read()
    encoded = base64.b64encode(img_data).decode()

    name = request.form["name"]
    from_email = FROM_EMAIL
    to_emails = []
    email_1 = (request.form["email"], request.form["name"])
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

    chat_id = os.getenv("GROUP_ID")
    updater.bot.sendChatAction(chat_id, action=ChatAction.TYPING)
    updater.bot.sendMessage(chat_id, f"New registration for {event_name}!")
    updater.bot.sendDocument(
        chat_id,
        document=open("qr.png", "rb"),
        caption=f"Name: {user.name} | ID: {user.id}",
    )

    return 'Please save this QR Code. It has also been emailed to you.<br><img src=\
            "data:image/png;base64, {}"/>'.format(
        encoded
    )


@app.route("/users", methods=["GET", "POST"])
def display_users():
    """Display the list of users in the desired database, after authentication."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == os.getenv("USERNAME"):
            if password == os.getenv("PASSWORD"):
                table = get_db_by_name(request.form["table"])
                user_data = db.session.query(table).order_by(asc(table.id))
                if user_data:
                    return render_template("users.html", users=user_data)
                return f"No users found in table {request.form['table']}"
            return "Invalid password!"
        return "Invalid user!"
    return """
            <form action="" method="post">
                <p><input type=text name=username required>
                <p><input type=password name=password required>
                <p>
                <select name="table" id="table">
                    <option value="codex_april_2019">CodeX April 2019</option>
                    <option value="eh_july_2019">Ethical Hacking July 2019</option>
                    <option value="cpp_workshop_may_2019">CPP Workshop May 2019</option>
                    <option value="rsc_2019">RSC 2019</option>
                    <option value="c_cpp_workshop_august_2019">C/C++ August 2019</option>
                    <option value="do_hacktoberfest_2019" selected>DigitalOcean Hacktoberfest 2019</option>
                </select>
                </p>
                <p><input type=submit value=Login>
            </form>
            """


@app.route("/csi_users", methods=["GET", "POST"])
def display_csi_users():
    """Display the list of users in the desired database, after authentication."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == os.getenv("CSI_USERNAME"):
            if password == os.getenv("CSI_PASSWORD"):
                table = get_db_by_name(request.form["table"])
                user_data = db.session.query(table).order_by(asc(table.id))
                if user_data:
                    return render_template(
                        "users.html",
                        users=user_data,
                        extra_columns={"prn": "PRN", "csi_id": "CSI ID"},
                    )
                return f"No users found in table {request.form['table']}"
            return "Invalid password!"
        return "Invalid user!"
    return """
            <form action="" method="post">
                <p><input type=text name=username required>
                <p><input type=password name=password required>
                <p>
                <select name="table" id="table">
                    <option value="csi_november_2019" selected>CSI Technovision</option>
                </select>
                </p>
                <p><input type=submit value=Login>
            </form>
            """


@app.route("/users_json")
def users_json():
    """Returns a JSON consisting of the users in the given table"""
    authorization_token = request.headers.get("Authorization")
    if authorization_token == os.getenv("AUTHORIZATION_TOKEN"):
        table = get_db_by_name(request.args.get("table"))
        user_data = db.session.query(table).order_by(asc(table.id))
        return users_to_json(user_data)
    elif authorization_token == os.getenv("CSI_AUTHORIZATION_TOKEN"):
        table = CSINovember2019
        user_data = db.session.query(table).order_by(asc(table.id))
        return users_to_json(user_data)
    return jsonify({"message": "Unauthorized"}), 401


@app.route("/csi")
def csi():
    return render_template(
        "csi.html",
        event="CSI Technovision",
        date="9th November 2019",
        db="csi_november_2019",
        year=True,
        extra_info="""Please only fill this form if you are a CSE student""",
    )


@app.route("/csi_submit", methods=["POST"])
def csi_submit():
    """Take data from the form, generate, display, and email QR code to user."""
    table = CSINovember2019
    event_name = request.form["event"]

    id = get_current_id(table)

    user = table(
        name=request.form["name"],
        email=request.form["email"],
        phone=request.form["phone_number"],
        id=id,
        department=request.form["department"],
        csi_id=request.form["csi_id"],
        year=request.form["year"],
        prn=request.form["prn"],
    )

    if request.form["whatsapp_number"]:
        user.phone += f"|{request.form['whatsapp_number']}"

    data = user.validate()
    if data is not True:
        return data

    try:
        db.session.add(user)
        db.session.commit()
    except exc.IntegrityError as e:
        print(e)
        return """It appears there was an error while trying to enter your data into our database.<br/>Kindly contact someone from the team and we will have this resolved ASAP"""

    img = generate_qr(request.form, user.csi_id)
    img.save("qr.png")
    img_data = open("qr.png", "rb").read()
    encoded = base64.b64encode(img_data).decode()

    name = request.form["name"]
    from_email = FROM_EMAIL
    to_emails = []
    email = (request.form["email"], request.form["name"])
    to_emails.append(email)
    date = request.form["date"]
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

    chat_id = "-390535990"
    updater.bot.sendChatAction(chat_id, action=ChatAction.TYPING)
    updater.bot.sendMessage(chat_id, f"New registration for {event_name}!")
    updater.bot.sendDocument(
        chat_id,
        document=open("qr.png", "rb"),
        caption=f"Name: {user.name} | ID: {user.csi_id}",
    )

    return 'Please save this QR Code. It has also been emailed to you.<br><img src=\
                "data:image/png;base64, {}"/>'.format(
        encoded
    )


@app.route("/")
def root():
    """Root endpoint. Displays the form to the user."""
    return "<marquee>Nothing here!</marquee>"


def get_current_id(table: db.Model):
    """Function to return the latest ID based on the database entries. 1 if DB is empty."""
    try:
        id = db.session.query(table).order_by(desc(table.id)).first().id
    except Exception:
        id = 0
    return int(id) + 1


def generate_qr(form_data, id):
    """Function to generate and return a QR code based on the given data."""
    return qrcode.make(
        "{}|{}|{}|{}|{}".format(
            form_data["event"],
            form_data["name"],
            form_data["email"],
            id,
            form_data["phone_number"],
        )
    )
