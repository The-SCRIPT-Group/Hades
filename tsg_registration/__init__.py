#!/usr/bin/env python3
"""
Flask application to accept some details, generate, display, and email a QR code to users
"""

# pylint: disable=invalid-name,too-few-public-methods,no-member,line-too-long,too-many-locals

import base64
import os
from datetime import datetime
from random import choice
from string import ascii_letters, digits
from urllib.parse import urlparse, urljoin

import qrcode
from flask import Flask, redirect, render_template, request, url_for, jsonify, abort
from flask_bcrypt import Bcrypt
from flask_login import (
    LoginManager,
    login_required,
    login_user,
    logout_user,
    current_user,
)
from flask_sqlalchemy import SQLAlchemy
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Attachment, Content, Mail
from sqlalchemy import desc, exc

import tsg_registration.telegram

bot_api_key = os.getenv("BOT_API_KEY")
tg = telegram.TG(bot_api_key)

FROM_EMAIL = os.getenv("FROM_EMAIL")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
bcrypt = Bcrypt(app)

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
    "email_content",
    "email_content_fields",
    "email_second_person",
    "event",
    "extra_field_telegram",
    "extra_message",
    "name_second_person",
    "whatsapp_number",
)

# Import event related classes
from tsg_registration.models.csi import CSINovember2019, CSINovemberNonMember2019
from tsg_registration.models.codex import CodexApril2019, RSC2019
from tsg_registration.models.techo import EHJuly2019, P5November2019
from tsg_registration.models.workshop import (
    CPPWSMay2019,
    CCPPWSAugust2019,
    Hacktoberfest2019,
    CNovember2019,
    BitgritDecember2019,
)

# Import miscellaneous classes
from tsg_registration.models.test import TestTable
from tsg_registration.models.user import Users
from tsg_registration.models.event import Events
from tsg_registration.models.user_access import Access

EVENT_CLASSES = {
    "codex_april_2019": CodexApril2019,
    "eh_july_2019": EHJuly2019,
    "cpp_workshop_may_2019": CPPWSMay2019,
    "rsc_2019": RSC2019,
    "c_cpp_workshop_august_2019": CCPPWSAugust2019,
    "do_hacktoberfest_2019": Hacktoberfest2019,
    "csi_november_2019": CSINovember2019,
    "csi_november_non_member_2019": CSINovemberNonMember2019,
    "p5_november_2019": P5November2019,
    "c_november_2019": CNovember2019,
    "bitgrit_december_2019": BitgritDecember2019,
    "test_users": TestTable,
    "access": Access,
    "users": Users,
    "events": Events,
}


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(Users).get(user_id)


@login_manager.request_loader
def load_user_from_request(request):
    credentials = request.headers.get("Credentials")
    if credentials:
        credentials = base64.b64decode(credentials).decode("utf-8")
        username, password = credentials.split("|")
        user = db.session.query(Users).get(username)
        if user is not None:
            if bcrypt.check_password_hash(user.password, password.strip()):
                return user
        return None
    api_key = request.headers.get("Authorization")
    if api_key:
        api_key = api_key.replace("Basic ", "", 1)
        users = db.session.query(Users).all()
        for user in users:
            if bcrypt.check_password_hash(user.api_key, api_key):
                return user

    return None


def get_table_by_name(name: str) -> db.Model:
    """Returns the database model class corresponding to the given name."""
    try:
        return EVENT_CLASSES[name]
    except KeyError:
        return None


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


@app.route("/submit", methods=["POST"])
def submit():
    """Take data from the form, generate, display, and email QR code to user."""
    table = get_table_by_name(request.form["db"])

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
        if int(user.phone) != int(request.form["whatsapp_number"]):
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
    if "email_content" in request.form and "email_content_fields" in request.form:
        d = {}
        for f in request.form["email_content_fields"].split(","):
            d[f] = request.form[f]

        message = request.form["email_content"].format(**d)
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
    if bot_api_key is not None:
        tg.send_chat_action(chat_id, "typing")
        tg.send_message(chat_id, f"New registration for {event_name}!")
        tg.send_document(chat_id, caption, "qr.png")

    return 'Please save this QR Code. It has also been emailed to you.<br><img src=\
            "data:image/png;base64, {}"/>'.format(
        encoded
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    """Display the list of users in the desired database, after authentication."""
    if request.method == "POST":
        user = request.form["username"]
        user = db.session.query(Users).filter_by(username=user).first()
        if user is not None:
            password = request.form["password"]
            if bcrypt.check_password_hash(user.password, password):
                login_user(user)
                next = request.args.get("next")
                if not is_safe_url(next):
                    return abort(400)
                return redirect(next or url_for("events"))
            return f"Wrong password for {user}!"
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            name = request.form["name"]
            username = request.form["username"]
            password = request.form["password"]
            email = request.form["email"]
        except KeyError:
            return jsonify({"response": "Please provide all required data"}), 400
        api_key = "".join(choice(ascii_letters + digits) for _ in range(32))
        u = Users(
            name=name,
            username=username,
            password=bcrypt.generate_password_hash(password).decode("utf-8"),
            email=email,
            api_key=bcrypt.generate_password_hash(api_key).decode("utf-8"),
        )
        try:
            db.session.add(u)
            db.session.commit()
        except exc.IntegrityError:
            return (
                jsonify(
                    {
                        "response": "Integrity constraint violated, please re-check your data!"
                    }
                ),
                400,
            )
        return (
            jsonify({"response": f"Hello {username}, your API Key is {api_key}!"}),
            200,
        )
    return render_template("register.html")


@app.route("/events", methods=["GET", "POST"])
@login_required
def events():
    if request.method == "POST":
        table = get_table_by_name(request.form["table"])
        user_data = db.session.query(table).all()
        columns = [c for c in table.__table__.columns._data.keys()]
        return render_template("users.html", users=user_data, columns=columns)
    accessible_tables = (
        db.session.query(Events)
        .filter(Users.username == current_user.username)
        .filter(Users.username == Access.user)
        .filter(Access.event == Events.name)
        .all()
    )
    return render_template("events.html", events=accessible_tables)


@app.route("/logout")
@login_required
def logout():
    name = current_user.name
    logout_user()
    return f"Logged out of {name}'s account!"


@app.route("/api/events")
@login_required
def events_api():
    """Returns a JSON consisting of the tables the user has the permission to view"""
    accessible_tables = (
        db.session.query(Events)
        .filter(Users.username == current_user.username)
        .filter(Users.username == Access.user)
        .filter(Access.event == Events.name)
        .all()
    )
    ret = {}
    for table in accessible_tables:
        ret[table.name] = table.full_name
    return jsonify(ret), 200


@app.route("/api/users", methods=["POST"])
@login_required
def users_api():
    """Returns a JSON consisting of the users in the given table"""
    try:
        table_name = request.form["table"]
    except KeyError:
        return jsonify({"response": "Please provide all required data"}), 400

    access = (
        db.session.query(Access)
        .filter(Access.user == current_user.username)
        .filter(Access.event == table_name)
    )
    if access is None:
        ret = (jsonify({"response": "Unauthorized"}), 401)
    else:
        table = get_table_by_name(request.form["table"])
        ret = (users_to_json(db.session.query(table).all()), 200)
    return ret


@app.route("/api/create", methods=["POST"])
@login_required
def create():
    try:
        table_name = request.form["table"]
    except KeyError:
        return jsonify({"response": "Please provide all required data"}), 400

    table = get_table_by_name(table_name)

    if table is None:
        return jsonify({"response": "Table does not exist!"}), 400

    access = (
        db.session.query(Access)
        .filter(Access.user == current_user.username)
        .filter(Access.event == table_name)
    )
    if access is None:
        return jsonify({"response": "Unauthorized"}), 401

    user_data = {}

    for k, v in request.form.items():
        if k == "table":
            continue
        user_data[k] = v
    user = table(**user_data)
    try:
        db.session.add(user)
        db.session.commit()
    except exc.IntegrityError:
        return (
            jsonify(
                {
                    "response": "Integrity constraint violated, please re-check your data!"
                }
            ),
            400,
        )
    return jsonify({"response": f"Created user {user} successfully!"}), 200


@app.route("/api/delete", methods=["DELETE"])
@login_required
def delete_user():
    try:
        table_name = request.form["table"]
        id = request.form["id"]
    except KeyError:
        return jsonify({"response": "Please provide all required data"}), 400
    access = (
        db.session.query(Access)
        .filter(Access.user == current_user.username)
        .filter(Access.event == table_name)
    )
    if access is None:
        return jsonify({"response": "Unauthorized"}), 401
    table = get_table_by_name(table_name)
    user = db.session.query(table).get(id)
    db.session.delete(user)
    db.session.commit()
    return f"Deleted user {user.name}"


@app.route("/api/update", methods=["PUT"])
@login_required
def update_user():
    try:
        table_name = request.form["table"]
        key = request.form["key"]
        data = request.form[key]
    except KeyError:
        return jsonify({"response": "Please provide all required data"}), 400
    access = (
        db.session.query(Access)
        .filter(Access.user == current_user.username)
        .filter(Access.event == table_name)
    )
    if access is None:
        return jsonify({"response": "Unauthorized"}), 401
    table = get_table_by_name(table_name)
    user = db.session.query(table).get(data)
    for k, v in request.form.items():
        if k in ("table", key):
            continue
        setattr(user, k, v)
    try:
        db.session.commit()
    except exc.IntegrityError:
        return (
            jsonify(
                {
                    "response": "Integrity constraint violated, please re-check your data!"
                }
            ),
            400,
        )
    return jsonify({"response": f"Updated user {user}"}), 200


@app.route("/api/sendmail", methods=["POST"])
@login_required
def send_mail():
    try:
        content = request.form["content"]
        subject = request.form["subject"]
        table_name = request.form["table"]
    except KeyError:
        return jsonify({"response": "Please provide all required data"}), 400
    access = (
        db.session.query(Access)
        .filter(Access.user == current_user.username)
        .filter(Access.event == table_name)
    )
    if access is None:
        return jsonify({"response": "Unauthorized"}), 401
    table = get_table_by_name(table_name)
    users = db.session.query(table).all()

    mail_content = Content("text/html", content)
    mail = Mail(FROM_EMAIL, FROM_EMAIL, subject, mail_content)
    for user in users:
        mail.add_bcc((user.email, user.name))
    try:
        SendGridAPIClient(SENDGRID_API_KEY).send(mail)
    except Exception as e:
        print(e)
        return jsonify({"response": "Failed to send mail"}), 500
    return jsonify({"response": "Sent mail"}), 200


@app.route("/bitgrit")
def bitgrit():
    return render_template(
        "form.html",
        date="4th December 2019",
        db="bitgrit_december_2019",
        department=True,
        extra_message="Timing is 1:30 - 5:30 pm on 4th December, 2019",
        event="Bitgrit Workshop",
        year=True,
    )


@app.route("/")
def root():
    """Root endpoint. Displays the form to the user."""
    return redirect(url_for("bitgrit"))


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
        if k == "_sa_instance_state" or k.split("_")[0] == "noqr":
            continue
        data += f"{v}|"
    return qrcode.make(data[:-1])
