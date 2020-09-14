#!/usr/bin/env python3
"""
Flask application to accept some details, generate, display, and email a QR code to users
"""

# pylint: disable=invalid-name,too-few-public-methods,no-member,line-too-long,too-many-locals
import binascii
from datetime import datetime
from urllib.parse import urlparse, urljoin

from decouple import config
from flask import Flask, redirect, render_template, url_for, jsonify, abort
from flask_login import (
    LoginManager,
    login_required,
    login_user,
    logout_user,
)
from flask_login.utils import login_url
from mongoengine import connect
from requests import post

app = Flask(__name__)
app.secret_key = config('SECRET_KEY')
app.config['JSON_SORT_KEYS'] = False

connect(
    config("DB_NAME"),
    host=config("DB_URI"),
    username=config('DB_USER'),
    password=config('DB_PASSWORD'),
)

login_manager = LoginManager()
login_manager.init_app(app)

from .db_utils import *

from .utils import *

from . import api

# Import event related classes
from . import models

# Import miscellaneous classes
from .models.user import Users, TSG

# A list of currently active events
ACTIVE_TABLES = [models.test.NewEvent]
ACTIVE_EVENTS = ['New Event']

# The list of fields that will be required for any and all form submissions
REQUIRED_FIELDS = ('name', 'phone', 'email')


def is_safe_url(target: str) -> bool:
    """Returns whether or not the target URL is safe or a malicious redirect"""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


@login_manager.user_loader
def load_user(user_id):
    """Return `User` object for the corresponding `user_id`"""
    return Users.objects(pk=user_id).first()


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
    if not credentials:
        credentials = request.headers.get('Authorization')
        if not credentials:
            return None

    # Cases where the header may be of the form `Authorization: Basic api_key`
    credentials = credentials.replace('Basic ', '', 1)

    try:
        credentials = base64.b64decode(credentials).decode('utf-8')
    except (UnicodeDecodeError, binascii.Error):
        return None
    username, password = credentials.split('|')
    user = get_user(Users, username)
    if user:
        if user.check_password_hash(password.strip()):
            log(
                f'User <code>{user.name}</code> just authenticated a {request.method} API call with credentials!',
            )
            return user
    return None


@login_manager.unauthorized_handler
def unauthorized():
    if 'Authorization' in request.headers or 'Credentials' in request.headers:
        return jsonify({'message': 'Access denied'}), 401

    # Generate the URL the login page should redirect to based on the URL user is trying to access in the same way
    # flask-login does so internally
    return redirect(login_url('login', request.url))


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

    # Ensure that we have the required fields
    for field in REQUIRED_FIELDS:
        if field not in request.form:
            return f'<code>{field}</code> is required but has not been submitted!'

    # ID is from a helper function that increments the latest ID by 1 and returns it
    id_ = get_current_id(table)

    data = {}

    # Ensure that we only take in valid fields to create our user object
    for k, v in request.form.items():
        if k in table._db_field_map.keys():
            data[k] = v

    # Instantiate our user object based on the received form data and retrived ID
    user = table(**data, id=id_)

    # If a separate WhatsApp number has been provided, store that in the database as well
    if 'whatsapp_number' in request.form and request.form['whatsapp_number'] != '':
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

    # Generate the QRCode based on the given data and store base64 encoded version of it to email
    if 'no_qr' not in request.form:
        img = generate_qr(user)
        img.save('qr.png')
        img_data = open('qr.png', 'rb').read()
        encoded = base64.b64encode(img_data).decode()

    # Add the user to the database, ensuring no integrity errors.
    success, reason = insert([user])
    if not success:
        log(f'Could not insert user {user}')
        log(reason)
        if reason == 'not_unique':
            return 'Someone else has already registered using these details! Kindly enter different values!'
        return """It appears there was an error while trying to enter your data into our database.<br/>Kindly contact someone from the team and we will have this resolved ASAP"""

    # Prepare the email sending
    from_email = config('FROM_EMAIL', default='noreply@thescriptgroup.in')
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
    subject = 'Registration for {} - {} - ID {}'.format(event_name, date, id_)
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

    # Take care of attachments, if any
    attachments = []
    if 'no_qr' not in request.form:
        attachments.append(
            {
                'data': encoded,
                'filename': 'qr.png',
                'type': 'image/png',
            }
        )

    # Send the mail
    mail_sent = send_mail(from_email, to_emails, subject, message, attachments)

    # Log the new entry to desired telegram channel
    chat_id = (
        request.form['chat_id'] if 'chat_id' in request.form else config('GROUP_ID')
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
        ret += "<br>Please save this QR Code. "
        if mail_sent:
            ret += "It has also been emailed to you."
        ret += "<br><img src=\
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
        user = get_user(Users, user)
        # Ensure user exists in the database
        if user is not None:
            password = request.form['password']
            # Check the password against the hash stored in the database
            if user.check_password_hash(password):
                # Log the login and redirect
                log(f'User <code>{user.name}</code> logged in via webpage!')
                login_user(user)
                next = request.args.get('next')
                if not is_safe_url(next):
                    return abort(400)
                return redirect(next or url_for('events'))
            return f'Wrong password for {user.username}!'
        return f"User <code>{request.form['username']}</code> doesn't exist!"
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
                return f'{field} is required!'
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # Create user object
        u = Users()
        u.name = name
        u.username = username
        u.generate_password_hash(password)
        u.email = email
        u.access = []

        # Add user object to list of objects to be inserted
        objects = [u]

        # If you're a TSG member, you get some access by default
        if is_user_tsg(email):
            u.access.append(Events.objects(pk='tsg').first())
            u.access.append(Events.objects(pk='test_users').first())

        success, reason = insert(objects)

        if not success:
            return f'Error occurred, {reason}', 400
        log(f'User <code>{u.name}</code> has been registered!')

        # Login to the new user account!
        login_user(u)

        return (
            f"Hello {username}, your account has been successfully created.<br/>You're logged into your account, feel "
            f"free to browse around "
        )

    # Logout current user before trying to register a new account
    if not current_user.is_anonymous:
        logout_user()
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
        user_data = get_data_from_table(table)
        return render_template(
            'users.html', users=user_data, columns=table._db_field_map.keys()
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
        # TODO: Use utils.update_user()
        if 'field' not in request.form:
            table_name = request.form['table']
            table = get_table_by_name(table_name)

            fields = table._db_field_map.keys()

            return render_template(
                'update.html',
                fields=fields,
                table_name=table_name,
            )

        table = get_table_by_name(request.form['table'])
        if table is None:
            return 'Table not chosen?'

        user = get_user(table, request.form['id'])
        success, reason = update_doc(user, request.form['field'], request.form['value'])

        if not success:
            return f'Error occurred trying to update - {reason}'

        log(
            f"<code>{current_user.name}</code> has updated <code>{request.form['field']}</code> of <code>{user}</code> to <code>{request.form['value']}</code>"
        )
        return 'User has been updated!'
    return render_template('events.html', events=get_accessible_tables())


@app.route('/delete', methods=['GET', 'POST'])
@login_required
def delete():
    """
    Displays a page with a dropdown to choose events on a GET request
    For POST, there for 2 cases
    If an `id` is not provided, it gets table table from the form and returns a page where user can choose an id
    If an id is provided, it deletes that id from the table
    """
    if request.method == 'POST':
        table_name = request.form['table']
        table = get_table_by_name(table_name)
        if 'id' not in request.form:
            user_data = get_data_from_table(table)

            return render_template(
                'delete.html', table_name=table_name, user_data=user_data
            )

        if table is None:
            return 'Table not chosen?'

        success, reason = utils.delete_user(request.form['id'], table_name)

        if not success:
            return f'Error occurred trying to delete - {reason}'

        log(
            f"<code>{current_user.name}</code> has deleted <code>{request.form['id']}</code> from {table_name}"
        )
        return (
            f"<code>{request.form['id']}</code> has been deleted from from {table_name}"
        )
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
        if current_user.check_password_hash(current_password):
            current_user.generate_password_hash(new_password)
        else:
            return 'Current password you entered is wrong! Please try again!'

        # Commit the changes we made in the object to the database
        success, reason = save_user(current_user)
        if not success:
            return f'Error occurred while changing your password - {reason}!'

        log(f'<code>{current_user.name}</code> has updated their password!</code>')

        # Log the user out, and redirect to login page
        logout_user()
        return redirect(url_for('login'))
    return render_template('change_password.html')


@app.route('/forgot_username', methods=['GET', 'POST'])
def forgot_username():
    if request.method == 'POST':
        if 'email' in request.form:
            email = request.form['email']
            user = Users.objects(email=email).first()
            if user:
                from_email = ('noreply@thescriptgroup.in', 'TSG Bot')
                to_email = [(user.email, user.name)]
                subject = 'Hades username'
                content = (
                    f"Hello {user.name}, your username is <code>{user.username}</code>!"
                )
                utils.send_mail(from_email, to_email, subject, content)
        return redirect(url_for('login'))
    return render_template('forgot_username.html')


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """Sends a password reset email"""
    if request.method == 'POST':
        if 'username' in request.form:
            username = request.form['username']
            user = Users.objects(pk=username)
            if user:
                reset_slug = utils.encrypt(username)
                reset_url = request.host_url + 'reset_password' + '/' + reset_slug
                from_email = ('noreply@thescriptgroup.in', 'TSG Bot')
                to_email = [(user.email, user.name)]
                subject = 'Password reset for Hades account'
                content = f"Hello {user.name}, please click <a href=\"{reset_url}\">here</a> to reset your password!"
                utils.send_mail(from_email, to_email, subject, content)
        return redirect(url_for('login'))
    return render_template('forgot_password.html')


@app.route('/reset_password/<string:slug>', methods=['GET', 'POST'])
def reset_password(slug: str):
    # Check whether link is still valid
    expiry = utils.extract_timestamp(slug) + 600
    if expiry < int(datetime.now().timestamp()):
        return "This password reset link has expired!"

    # Retrieve the username
    username = utils.decrypt(slug)
    if request.method == 'POST':
        form_username = request.form['username']
        if username != form_username:
            log(f'{form_username} just tried to use reset link for {username}!')
            return f'This link is not valid for {form_username}!'

        # Update password
        password = request.form['new_password']
        user = Users.objects(pk=username)
        user.generate_password_hash(password)

        # Commit the changes we made in the object to the database
        success, reason = save_user(user)
        if not success:
            return f'Error occurred while changing your password - {reason}!'
        return 'Your password has been successfully changed!'
    return render_template('reset_password.html', username=username)


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
    return render_template('index.html')


@app.route("/form")
def form():
    return render_template(
        "form.html",
        date="14th September, 2020",
        db="new_event",
        event="New Event",
    )
