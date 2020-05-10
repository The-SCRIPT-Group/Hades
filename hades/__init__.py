#!/usr/bin/env python3
"""
Flask application to accept some details, generate, display, and email a QR code to users
"""

# pylint: disable=invalid-name,too-few-public-methods,no-member,line-too-long,too-many-locals

import base64
import os
from datetime import datetime
from random import choice
from string import ascii_letters, digits, punctuation

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
from sqlalchemy import inspect
from sqlalchemy.exc import DataError, IntegrityError

from hades.telegram import TG
from hades.utils import (
    log,
    get_table_by_name,
    get_current_id,
    generate_qr,
    tg,
    is_safe_url,
    get_accessible_tables,
)

FROM_EMAIL = os.getenv('FROM_EMAIL')
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
bcrypt = Bcrypt(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

# Import event related classes
from hades.models.csi import CSINovember2019, CSINovemberNonMember2019
from hades.models.codex import CodexApril2019, RSC2019, CodexDecember2019, BOV2020
from hades.models.giveaway import Coursera2020
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
from hades.models.user import Users, TSG
from hades.models.event import Events
from hades.models.user_access import Access

ACTIVE_TABLES = [Coursera2020]
ACTIVE_EVENTS = ['Coursera 2020']


@login_manager.user_loader
def load_user(user_id):
    """Return `User` object for the corresponding `user_id`"""
    return db.session.query(Users).get(user_id)


@login_manager.request_loader
def load_user_from_request(request):
    """Checks for authorization in a request

    The request can contain one of 2 headers
    -> Credentials: base64(username|password)
    or
    -> Authorization: api_token

    It first checks for the `Credentials` header, and then for `Authorization`
    If they match any user in the database, that user is logged into that session
    """
    credentials = request.headers.get('Credentials')
    if credentials:
        try:
            credentials = base64.b64decode(credentials).decode('utf-8')
        except UnicodeDecodeError:
            return (
                jsonify(
                    {
                        'response': 'UnicodeDecodeError, what kinda data did you even pass?'
                    }
                ),
                400,
            )
        username, password = credentials.split('|')
        user = db.session.query(Users).get(username)
        if user is not None:
            if bcrypt.check_password_hash(user.password, password.strip()):
                log(
                    f'User <code>{user.name}</code> just authenticated a {request.method} API call with credentials!',
                )
                return user
        return None
    api_key = request.headers.get('Authorization')
    if api_key:
        # Cases where the header may be of the form `Authorization: Basic api_key`
        api_key = api_key.replace('Basic ', '', 1)
        users = db.session.query(Users).all()
        for user in users:
            if bcrypt.check_password_hash(user.api_key, api_key):
                log(
                    f'User <code>{user.name}</code> just authenticated a {request.method} API call with an API key!',
                )
                return user

    return None


@app.route('/submit', methods=['POST'])
def submit():
    """Accepts form data for an event registration

    Some required fields are
    db -> The name of the database corresponding to the event. This will be hardcoded as an invisible uneditable field
    event -> The name of the event

    These fields can be skipped if ACTIVE_TABLES and ACTIVE_EVENTS lists have only one element
    This is done as we usually don't have more than 1 event at one time, we can reduce the risk of data being changed
    at the frontend by directly setting it here in the backend

    The rest of the parameters vary per event, we check the keys in the form items against the attributes of the
    corresponding event class to ensure that no extraneous data is accepted

    Some required ones are
    -> name - Person's name
    -> email - Person's email address
    -> department - Person's department

    Some optional fields which are *NOT* members of any class
    -> no_qr - To disable QR generation and attachment in email
    -> whatsapp_number - To store WhatsApp number separately
    -> chat_id - Alternative Telegram Chat ID where registrations should be logged
    -> email_content - Alternative email content to be sent to user
    -> email_formattable_content - content where some field needs to be replaced with the fields in email_content_fields
    -> email_content_fields - list of additional form fields which need to be replaced with variable's value in the email_formattable_content
    -> extra_message - Extra information to be appended to end of email
    -> extra_field_telegram - If anything besides ID and name are to be logged to Telegram, it is specified here

    The next three are specifically for events with group registrations
    -> name_second_person
    -> email_second_person
    -> department_second_person

    These are self explanatory

    Based on the data, a QR code is generated, displayed, and also emailed to the user(s).
    """

    # If there's just one active table, no need of checking
    if len(ACTIVE_TABLES) == 1:
        table = ACTIVE_TABLES[0]
    elif 'db' in request.form:
        table = get_table_by_name(request.form['db'])
        # Ensure that the provided table is active
        if table not in ACTIVE_TABLES:
            print(request.form)

            print(request.form['db'])
            log(
                f"Someone just tried to register to table <code>{request.form['db']}</code>"
            )
            form_data = ''
            for k, v in request.form.items():
                form_data += f'<code>{k}</code> - <code>{v}</code>\n'
            log(f'Full form:\n{form_data[:-1]}')
            return "That wasn't a valid db..."
    else:
        return "You need to specify a database!"

    # If we have only one active event - we know the event name already
    if len(ACTIVE_EVENTS) == 1:
        event_name = ACTIVE_EVENTS[0]
    elif 'event' in request.form:
        event_name = request.form['event']
    else:
        return 'Hades does require the event name, you know?'

    # ID is from a helper function that increments the latest ID by 1 and returns it
    id = get_current_id(table)

    data = {}

    # Ensure that we only take in valid fields to create our user object
    for k, v in request.form.items():
        if k in table.__table__.columns._data.keys():
            data[k] = v

    # Instantiate our user object based on the received form data and retrived ID
    user = table(**data, id=id)

    # If a separate WhatsApp number has been provided, store that in the database as well
    if 'whatsapp_number' in request.form:
        try:
            if int(user.phone) != int(request.form['whatsapp_number']):
                user.phone += f"|{request.form['whatsapp_number']}"
        except (TypeError, ValueError) as e:
            form_data = ''
            for k, v in request.form.items():
                form_data += f'<code>{k}</code> - <code>{v}</code>\n'
            log(f'Exception on WhatsApp Number:\n{form_data[:-1]}')
            log(e)
            return "That wasn't a WhatsApp number..."

    # Store 2nd person's details ONLY if all 3 required parameters have been provided
    if (
        'name_second_person' in request.form
        and 'email_second_person' in request.form
        and 'department_second_person' in request.form
    ):
        user.name += f", {request.form['name_second_person']}"
        user.email += f", {request.form['email_second_person']}"
        user.department += f", {request.form['department_second_person']}"

    # Ensure that no data is duplicated. If anything is wrong, display the corresponding error to the user
    data = user.validate()
    if data is not True:
        return data

    # Generate the QRCode based on the given data and store base64 encoded version of it to email
    if 'no_qr' not in request.form:
        img = generate_qr(user)
        img.save('qr.png')
        img_data = open('qr.png', 'rb').read()
        encoded = base64.b64encode(img_data).decode()

    # Add the user to the database and commit the transaction, ensuring no integrity errors.
    try:
        db.session.add(user)
        db.session.commit()
    except (IntegrityError, DataError) as e:
        print(e)
        return """It appears there was an error while trying to enter your data into our database.<br/>Kindly contact someone from the team and we will have this resolved ASAP"""

    # Prepare the email sending
    from_email = FROM_EMAIL
    to_emails = []
    email_1 = (request.form['email'], request.form['name'])
    to_emails.append(email_1)
    if (
        'email_second_person' in request.form
        and 'name_second_person' in request.form
        and request.form['email'] != request.form['email_second_person']
    ):
        email_2 = (
            request.form['email_second_person'],
            request.form['name_second_person'],
        )
        to_emails.append(email_2)

    # Check if the form specified the date, otherwise use the current month and year
    if 'date' in request.form:
        date = request.form['date']
    else:
        date = datetime.now().strftime('%B,%Y')
    subject = 'Registration for {} - {} - ID {}'.format(event_name, date, id)
    message = """<img src='https://drive.google.com/uc?id=12VCUzNvU53f_mR7Hbumrc6N66rCQO5r-&export=download' style='width:30%;height:50%'>
<hr>
{}, your registration is done!
<br/>
""".format(
        user.name
    )
    if 'no_qr' not in request.form:
        message += """A QR code has been attached below!
<br/>
You're <b>required</b> to present this on the day of the event."""
    if (
        'email_formattable_content' in request.form
        and 'email_content_fields' in request.form
    ):
        d = {}
        for f in request.form['email_content_fields'].split(','):
            d[f] = request.form[f]
        message = ''
        if 'email_content' in request.form:
            message += request.form['email_content']
        message += request.form['email_formattable_content'].format(**d)

    if 'extra_message' in request.form:
        message += '<br/>' + request.form['extra_message']

    # Set the email content, recepients, sender, and the subject
    content = Content('text/html', message)
    mail = Mail(from_email, to_emails, subject, html_content=content)

    if 'no_qr' not in request.form:
        # Add the base64 encoded QRCode as an attachment with mimetype image/png
        mail.add_attachment(Attachment(encoded, 'qr.png', 'image/png'))

    # Actually send the mail. Print the errors if any.
    try:
        response = SendGridAPIClient(SENDGRID_API_KEY).send(mail)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e)
        print(e.body)

    # Log the new entry to desired telegram channel
    chat_id = (
        request.form['chat_id'] if 'chat_id' in request.form else os.getenv('GROUP_ID')
    )
    caption = f'Name: {user.name} | ID: {user.id}'
    if 'extra_field_telegram' in request.form:
        caption += f" | {request.form['extra_field_telegram']} - {request.form[request.form['extra_field_telegram']]}"

    tg.send_chat_action(chat_id, 'typing')
    tg.send_message(chat_id, f'New registration for {event_name}!')
    if 'no_qr' not in request.form:
        tg.send_document(chat_id, caption, 'qr.png')
    else:
        tg.send_message(chat_id, caption)

    ret = f'Thank you for registering, {user.name}!'
    if 'no_qr' not in request.form:
        ret += "<br>Please save this QR Code. It has also been emailed to you.<br><img src=\
                'data:image/png;base64, {}'/>".format(
            encoded
        )
    else:
        ret += '<br>Please check your email for confirmation.'
    return ret


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Displays a login page on a GET request
    For POST, it checks the `username` and `password` provided and accordingly redirects to desired page
    (events page if none specified)

    It *will* abort with a 400 error if the `next` parameter is trying to redirect to an unsafe URL
    """
    if request.method == 'POST':
        user = request.form['username']
        user = db.session.query(Users).filter_by(username=user).first()
        # Ensure user exists in the database
        if user is not None:
            password = request.form['password']
            # Check the password against the hash stored in the database
            if bcrypt.check_password_hash(user.password, password):
                # Log the login and redirect
                log(f'User <code>{user.name}</code> logged in via webpage!')
                login_user(user)
                next = request.args.get('next')
                if not is_safe_url(next):
                    return abort(400)
                return redirect(next or url_for('events'))
            return f'Wrong password for {user.username}!'
        return f"{request.form['username']} doesn't exist!"
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Displays a registration page on a GET request
    For POST, it checks the `name`, `email`, `username` and `password` provided and accordingly registers account

    A random 32 character API key is generated and displayed

    Password and API key are hashed before being stored in the database
    """
    if request.method == 'POST':
        required_fields = ('name', 'username', 'password', 'email')
        for field in required_fields:
            if field not in request.form:
                return jsonify({'response': f'{field} is required!'}), 400
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # Generate API key
        api_key = ''.join(
            choice(ascii_letters + digits + punctuation) for _ in range(32)
        )
        # Create user object
        u = Users(
            name=name,
            username=username,
            password=bcrypt.generate_password_hash(password).decode('utf-8'),
            email=email,
            api_key=bcrypt.generate_password_hash(api_key).decode('utf-8'),
        )
        # Add the user object to the database
        db.session.add(u)

        # If you're a TSG member, you get some access by default
        if db.session.query(TSG).filter(TSG.email == email).first():
            db.session.add(Access('tsg', username))
            db.session.add(Access('test_users', username))

        # Commit the transaction and confirm that no integrity constraints have been violated
        try:
            db.session.commit()
        except IntegrityError:
            return (
                jsonify(
                    {
                        'response': 'Integrity constraint violated, please re-check your data!'
                    }
                ),
                400,
            )
        log(f'User <code>{u.name}</code> account has been registered!')
        return f"Hello {username}, your account has been successfully created.<br>If you wish to use an API Key for sending requests, your key is <code>{api_key}</code><br/>Don't share it with anyone, if you're unsure of what it is, you don't need it"
    return render_template('register.html')


@app.route('/events', methods=['GET', 'POST'])
@login_required
def events():
    """
    Displays a page with a dropdown to choose events on a GET request
    For POST, it checks the `table` provided and accordingly returns a table listing the users in that table
    """
    if request.method == 'POST':
        if 'table' not in request.form:
            return jsonify(
                {'response': 'Please specify the table you want to access!'}, 400
            )
        table_name = request.form['table']
        table = get_table_by_name(table_name)
        if table is None:
            return jsonify({'response': f'Table {table} does not seem to exist!'}, 400)
        log(
            f"User <code>{current_user.name}</code> is accessing <code>{request.form['table']}</code>!"
        )
        user_data = db.session.query(table).all()
        return render_template(
            'users.html', users=user_data, columns=table.__table__.columns._data.keys()
        )
    return render_template('events.html', events=get_accessible_tables())


@app.route('/update', methods=['GET', 'POST'])
@login_required
def update():
    """
    Displays a page with a dropdown to choose events on a GET request
    For POST, there for 2 cases
    If a `field` is not provided, it gets table table from the form and returns a page where user can choose a field
    If a field is provided, that field of the corresponding user is updated (table and a key attribute are taken from
    the form as well)
    """
    if request.method == 'POST':
        if 'field' not in request.form:
            table_name = request.form['table']
            table = get_table_by_name(table_name)
            i = inspect(table)
            fields = i.columns.keys()
            for f in fields:
                if i.columns[f].primary_key or i.columns[f].unique:
                    fields.remove(f)

            return render_template('update.html', fields=fields, table_name=table_name,)

        table = get_table_by_name(request.form['table'])
        if table is None:
            return 'Table not chosen?'

        user = db.session.query(table).get(request.form[request.form['key']])
        setattr(user, request.form['field'], request.form['value'])

        try:
            db.session.commit()
        except IntegrityError:
            return 'Integrity constraint violated, please re-check your data!'

        log(
            f"<code>{current_user.name}</code> has updated <code>{request.form['field']}</code> of <code>{user}</code> to <code>{request.form['value']}</code>"
        )
        return 'User has been updated!'
    return render_template('events.html', events=get_accessible_tables())


@app.route('/changepassword', methods=['GET', 'POST'])
@login_required
def change_password():
    """
       Displays a page to enter current and a new password on a GET request
       For POST, changes the password if current one matches and logs you out
    """

    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']

        # If current password is correct, update and store the new hash
        if bcrypt.check_password_hash(current_user.password, current_password):
            current_user.password = bcrypt.generate_password_hash(new_password)
        else:
            return 'Current password you entered is wrong! Please try again!'

        # Complete the transaction. No exceptions should occur here
        db.session.commit()

        log(f'<code>{current_user.name}</code> has updated their password!</code>')

        # Log the user out, and redirect to login page
        logout_user()
        return redirect(url_for('login'))
    return render_template('change_password.html')


@app.route('/logout')
@login_required
def logout():
    """Logs the current user out"""
    name = current_user.name
    logout_user()
    return f"Logged out of {name}'s account!"


@app.route('/')
def root():
    """Root endpoint. Displays the form to the user."""
    return '<marquee>Nothing here!</marquee>'
