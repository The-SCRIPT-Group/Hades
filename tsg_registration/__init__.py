#!/usr/bin/env python3
"""
Flask application to accept some details, generate, display, and email a QR code to users
"""

# pylint: disable=invalid-name,too-few-public-methods,no-member,line-too-long,too-many-locals

import base64
import os

from datetime import datetime

import qrcode
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Attachment, Content, Mail, Personalization

from flask import Flask, redirect, render_template, request, url_for
from sqlalchemy import desc, exc
from flask_sqlalchemy import SQLAlchemy

FROM_EMAIL = os.getenv("FROM_EMAIL")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

app = Flask(__name__)
db = SQLAlchemy(app)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")


DEPARTMENTS = {
    "cse": "Computer Science and Engineering",
    "ece": "Electronics and Communication Engineering",
    "mech": "Mechanical Engineering",
    "civil": "Civil Engineering",
    "chem": "Chemical Engineering",
    "others": "Others",
}

from tsg_registration.models.codex import CodexApril2019, RSC2019
from tsg_registration.models.techo import EHJuly2019
from tsg_registration.models.workshop import CPPWSMay2019


def get_db_by_name(name: str) -> db.Model:
    if name == "codex_april_2019":
        return CodexApril2019
    if name == "cpp_workshop_may_2019":
        return CPPWSMay2019
    if name == "eh_july_2019":
        return EHJuly2019
    return RSC2019


@app.route("/submit", methods=["POST"])
def submit():
    """
    Take data from the form, generate, display, and email QR code to user
    """
    table = get_db_by_name(request.form["db"])
    event_name = request.form["event"]
    for user in db.session.query(table).all():
        if request.form["email"] == user.email:
            return "Email address {} already found in database!\
            Please re-enter the form correctly!".format(
                request.form["email"]
            )

        if str(request.form["phone_number"]) == str(user.phone):
            return "Phone number {} already found in database!\
            Please re-enter the form correctly!".format(
                request.form["phone_number"]
            )

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

    if request.form['whatsapp_number'] is not None:
        user.phone += f"|{request.form['whatsapp_number']}"

    try:
        db.session.add(user)
        db.session.commit()
    except exc.IntegrityError as e:
        print(e)
        return "Error occurred trying to enter values into the database!"

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
    message = """<img src='https://drive.google.com/uc?id=12VCUzNvU53f_mR7Hbumrc6N66rCQO5r-&export=download' style="width:50%;height:50%">
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

    return 'Please save this QR Code. It has also been emailed to you.<br><img src=\
            "data:image/png;base64, {}"/>'.format(
        encoded
    )


@app.route("/users", methods=["GET", "POST"])
def display_users():
    """
    Display the list of users, after authentication
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == os.getenv("USERNAME"):
            if password == os.getenv("PASSWORD"):
                table = get_db_by_name(request.form["table"])
                user_data = db.session.query(table).all()
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
                    <option value="rsc_2019" selected>RSC 2019</option>
                </select>
                </p>
                <p><input type=submit value=Login>
            </form>
            """


@app.route("/codex")
def codex():
    return redirect(url_for("/"))


@app.route("/techo")
def techo():
    return redirect(url_for("/"))


@app.route("/")
def root():
    """
    Main endpoint. Display the form to the user.
    """
    return render_template('form.html', event='Ready Set Code 2019', group=False, department=True,
                           date='5th and 7th August 2019', db='rsc_2019', year=True)


def get_current_id(table: db.Model):
    """
    Function to return the latest ID
    """
    try:
        id = db.session.query(table).order_by(desc(table.id)).first().id
    except Exception:
        id = 0
    return int(id) + 1


def generate_qr(form_data, id):
    """
    Function to generate and return a QR code based on the given data
    """
    return qrcode.make(
        "\nName: {}\nEmail: {}\nID: {}\nPhone Number: {}".format(
            form_data["name"], form_data["email"], id, form_data["phone_number"]
        )
    )
