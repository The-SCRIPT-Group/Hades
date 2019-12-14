#!/usr/bin/env python3
"""
Flask application to accept some details, generate, display, and email a QR code to users
"""

# pylint: disable=invalid-name,too-few-public-methods,no-member,line-too-long,too-many-locals

import base64
import os
from datetime import datetime
from json import loads
from random import choice
from string import ascii_letters, digits, punctuation
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
from requests import put
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Attachment, Content, Mail
from sqlalchemy import desc, exc

import hades.telegram

bot_api_key = os.getenv("BOT_API_KEY")
tg = telegram.TG(bot_api_key)

log_channel = os.getenv("LOG_ID")

FROM_EMAIL = os.getenv("FROM_EMAIL")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
bcrypt = Bcrypt(app)

from hades.utils import users_to_json

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")

DEPARTMENTS = {
    "cse": "Computer Science and Engineering",
    "mtech": "M.Tech",
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
from hades.models.csi import CSINovember2019, CSINovemberNonMember2019
from hades.models.codex import CodexApril2019, RSC2019, CodexDecember2019
from hades.models.techo import EHJuly2019, P5November2019
from hades.models.workshop import (
    CPPWSMay2019,
    CCPPWSAugust2019,
    Hacktoberfest2019,
    CNovember2019,
    BitgritDecember2019,
)

# Import miscellaneous classes
from hades.models.test import TestTable
from hades.models.user import Users
from hades.models.event import Events
from hades.models.user_access import Access

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
    "codex_december_2019": CodexDecember2019,
}


def log(message):
    tg.send_message(log_channel, f"<b>Hades</b>: {message}")


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
                log(
                    f"User <code>{user.name}</code> just authenticated a {request.method} API call with credentials!",
                )
                return user
        return None
    api_key = request.headers.get("Authorization")
    if api_key:
        api_key = api_key.replace("Basic ", "", 1)
        users = db.session.query(Users).all()
        for user in users:
            if bcrypt.check_password_hash(user.api_key, api_key):
                log(
                    f"User <code>{user.name}</code> just authenticated a {request.method} API call with an API key!",
                )
                return user

    return None


def check_access(table_name: str):
    log(
        f"User <code>{current_user.name}</code> trying to access <code>{table_name}</code>!",
    )
    return (
        db.session.query(Access)
        .filter(Access.user == current_user.username)
        .filter(Access.event == table_name)
    )


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

    if request.form["name_second_person"] and request.form["email_second_person"]:
        user.name += f", {request.form['name_second_person']}"
        user.email += f", {request.form['email_second_person']}"

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

    from_email = FROM_EMAIL
    to_emails = []
    email_1 = (request.form["email"], request.form["name"])
    to_emails.append(email_1)
    if (
        request.form["email_second_person"]
        and request.form["name_second_person"]
        and request.form["email"] != request.form["email_second_person"]
    ):
        email_2 = (
            request.form["email_second_person"],
            request.form["name_second_person"],
        )
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
        user.name
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
        print(e.body)

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
                log(f"User <code>{user.name}</code> logged in via webpage!")
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
        api_key = "".join(
            choice(ascii_letters + digits + punctuation) for _ in range(32)
        )
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
        log(f"User <code>{u.name}</code> account has been registered!")
        return f"Hello {username}, your account has been successfully created.<br>If you wish to use an API Key for sending requests, your key is <code>{api_key}</code><br/>Don't share it with anyone, if you're unsure of what it is, you don't need it"
    return render_template("register.html")


@app.route("/events", methods=["GET", "POST"])
@login_required
def events():
    if request.method == "POST":
        table = get_table_by_name(request.form["table"])
        if table is None:
            return "How exactly did you reach here?"
        log(
            f"User <code>{current_user.name}</code> is accessing <code>{request.form['table']}</code>!",
        )
        user_data = db.session.query(table).all()
        return render_template(
            "users.html", users=user_data, columns=table.__table__.columns._data.keys()
        )
    accessible_tables = (
        db.session.query(Events)
        .filter(Users.username == current_user.username)
        .filter(Users.username == Access.user)
        .filter(Access.event == Events.name)
        .all()
    )
    return render_template("events.html", events=accessible_tables)


@app.route("/update", methods=["GET", "POST"])
@login_required
def update():
    if request.method == "POST":
        if "field" not in request.form:
            table = get_table_by_name(request.form["table"])
            return render_template(
                "update.html", fields=table.__table__.columns._data.keys(),
            )
        payload = {
            "table": request.form["table"],
            "key": "id",
            "id": request.form["id"],
            request.form["field"]: request.form["value"],
        }
        return loads(
            put(
                url="https://hades.thescriptgroup.in/api/update",
                data=payload,
                headers=request.headers,
            ).text
        )["response"]
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


@app.route("/api/authenticate", methods=["POST"])
@login_required
def authenticate_api():
    return (
        jsonify({"message": f"Successfully authenticated as {current_user.username}"}),
        200,
    )


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


@app.route("/api/users")
@login_required
def users_api():
    """Returns a JSON consisting of the users in the given table"""
    table_name = request.args.get("table")
    if not table_name:
        return jsonify({"response": "Please provide all required data"}), 400

    access = check_access(table_name)
    if access is None:
        return jsonify({"response": "Unauthorized"}), 401
    table = get_table_by_name(table_name)
    if table is None:
        return jsonify({"response": f"Table {table_name} does not exist!"}), 400
    return users_to_json(db.session.query(table).all()), 200


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

    access = check_access(table_name)
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
    log(
        f"User <code>{user}</code> has been created in table <code>{table_name}</code>!",
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
    access = check_access(table_name)
    if access is None:
        return jsonify({"response": "Unauthorized"}), 401
    table = get_table_by_name(table_name)
    user = db.session.query(table).get(id)
    db.session.delete(user)
    db.session.commit()
    log(
        f"User <code>{current_user.name}</code> has deleted <code>{user}</code> from <code>{table_name}</code>!",
    )
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
    access = check_access(table_name)
    if access is None:
        return jsonify({"response": "Unauthorized"}), 401
    table = get_table_by_name(table_name)
    user = db.session.query(table).get(data)
    for k, v in request.form.items():
        if k in ("key", "table", key):
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
    log(
        f"User <code>{current_user.name}</code> has updated <code>{user}</code> in <code>{table_name}</code>!",
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
    access = check_access(table_name)
    if access is None:
        return jsonify({"response": "Unauthorized"}), 401
    table = get_table_by_name(table_name)
    users = db.session.query(table).all()

    mail_content = Content("text/html", content)
    mail = Mail(FROM_EMAIL, FROM_EMAIL, subject, mail_content)
    for user in users:
        if "," in user.name:
            mail.add_bcc((user.email.split(",")[0], user.name.split(",")[0]))
            mail.add_bcc(
                (user.email.split(",")[1].rstrip(), user.name.split(",")[1].rstrip())
            )
    try:
        SendGridAPIClient(SENDGRID_API_KEY).send(mail)
    except Exception as e:
        print(e)
        return jsonify({"response": "Failed to send mail"}), 500
    log(
        f"User <code>{current_user.name}</code> has sent mail <code>{content}</code> with subject <code>{subject}</code> to <code>{table_name}</code>!",
    )
    return jsonify({"response": "Sent mail"}), 200


@app.route("/codex")
def codex():
    return render_template(
        "form.html",
        date="19th December, 2019",
        db="codex_december_2019",
        department=True,
        event="CodeX December 2019",
        group=True,
        miscellaneous="""<input type="text" name="hackerrank_username" placeholder="Enter your HackerRank username" maxlength="50" required class="form-control" pattern="^\w*$"/>
                <hr>
                <p>Payment Method</p>
                <select name="noqr_paid" class="form-control" id="noqr_paid" required>
                    <option value="paytm">PayTM Gateway</option>
                    <option value="cash">Cash</option>
                </select>
                <hr>
        """,
        year=True,
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


def generate_qr(user):
    """Function to generate and return a QR code based on the given data."""
    data = ""
    for k, v in user.__dict__.items():
        if k == "_sa_instance_state" or k.split("_")[0] == "noqr":
            continue
        data += f"{v}|"
    return qrcode.make(data[:-1])
