import os
from json import dumps
from urllib.parse import urlparse, urljoin

from flask import request
from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from hades import db, TG, DATABASE_CLASSES

# Retrieve telegram bot API key
from hades.models.event import Events
from hades.models.user import Users
from hades.models.user_access import Access

bot_api_key = os.getenv('BOT_API_KEY')

# Initialize object for sending messages to telegram
tg = TG(bot_api_key)

# Retrieve ID of Telegram log channel
log_channel = os.getenv('LOG_ID')


def validate(data, table):
    # Ensure nobody else in the table has the same email address
    if db.session.query(table).filter(table.email == data.email).first():
        return f'Email address {data.email} already found in database! Please re-enter the form correctly!'

    # Ensure nobody else int he table has the same phone number
    for num in data.phone.split('|'):
        if db.session.query(table).filter(table.phone.like(f'%{num}%')).first():
            return f'Phone number {num} already found in database! Please re-enter the form correctly!'

    return True


def users_to_json(users):
    json_data = []
    for user in users:
        user_data = {}
        for k, v in user.__dict__.items():
            if k == '_sa_instance_state':
                continue
            user_data[k] = v
        json_data.append(user_data)

    return dumps(json_data)


def log(message: str):
    """Logs the given `message` to our Telegram logging channel"""
    tg.send_message(log_channel, f'<b>Hades</b>: {message}')


def check_access(table_name: str) -> bool:
    """Returns whether or not the currently logged in user has access to `table_name`"""
    log(
        f'User <code>{current_user.name}</code> trying to access <code>{table_name}</code>!',
    )
    return (
        db.session.query(Access)
        .filter(Access.user == current_user.username)
        .filter(Access.event == table_name)
    )


def get_table_by_name(name: str) -> db.Model:
    """Returns the database model class corresponding to the given name."""
    return DATABASE_CLASSES.get(name)


def is_safe_url(target: str) -> bool:
    """Returns whether or not the target URL is safe or a malicious redirect"""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def get_accessible_tables():
    """Returns the list of tables the currently logged in user can access"""
    return (
        db.session.query(Events)
        .filter(Users.username == current_user.username)
        .filter(Users.username == Access.user)
        .filter(Access.event == Events.name)
        .all()
    )


def update_user(id: int, table_name: str, user_data: dict) -> (bool, str):
    """
    :param id -> User ID
    :param table_name -> Name of the table
    :param user_data -> Dictionary containing fields to be updated
    :return success/failure, reasoning
    """

    table = get_table_by_name(table_name)

    if table is None:
        return False, f'Table {table_name} does not seem to exist!'

    user = db.session.query(table).get(id)
    if user is None:
        return False, f'Table {table_name} does not have a user with ID {id}'

    for k, v in user_data.items():
        setattr(user, k, v)

    try:
        db.session.commit()
    except IntegrityError as e:
        return (
            False,
            f'You violated an integrity constraint trying to update {id} in {table_name} with {user_data}!',
        )
    return True, f'{user} has been successfully updated!'


def delete_user(id: int, table_name: str) -> (bool, str):
    """
    :param id -> User ID
    :param table_name -> Name of the table user is to be deleted from
    :return success/failure, reasoning
    """

    table = get_table_by_name(table_name)

    if table is None:
        return False, f'Table {table_name} does not seem to exist!'

    user = db.session.query(table).get(id)
    if user is None:
        return False, f'Table {table_name} does not have a user with ID {id}'

    db.session.delete(user)
    log(
        f'User <code>{current_user.name}</code> has deleted <code>{user}</code> from <code>{table_name}</code>!'
    )
    try:
        db.session.commit()
    except Exception as e:
        log(f'Exception occurred in above deletion!')
        log(e)
        return False, f'Exception occurred trying to delete {id} from {table_name}!'
    return True, f'{user} deleted successfully!'


def get_current_id(table):
    """Function to return the latest ID based on the database entries. 1 if DB is empty."""
    try:
        id = db.session.query(table).order_by(desc(table.id)).first().id
    except Exception:
        id = 0
    return int(id) + 1


def generate_qr(user):
    """Function to generate and return a QR code based on the given data."""
    data = {k: v for k, v in user.__dict__.items() if k not in QR_BLACKLIST}
    data['table'] = user.__tablename__
    return qrcode.make(base64.b64encode(dumps(data).encode()))
