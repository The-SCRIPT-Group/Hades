import base64
from json import dumps

import qrcode
from cryptography.fernet import Fernet
from decouple import config
from flask import request
from flask_login import current_user
from mongoengine import DynamicDocument
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Attachment, Content, Mail

from .db_utils import *
from .models.codex import CodexApril2019, RSC2019, CodexDecember2019, BOV2020
from .models.csi import CSINovember2019, CSINovemberNonMember2019
from .models.event import Events
from .models.giveaway import Coursera2020
from .models.techo import EHJuly2019, P5November2019
from .models.test import TestTable
from .models.user import Users
from .models.workshop import (
    CPPWSMay2019,
    CCPPWSAugust2019,
    Hacktoberfest2019,
    CNovember2019,
    BitgritDecember2019,
)
from .telegram import TG

# SendGrid API Key
SENDGRID_API_KEY = config('SENDGRID_API_KEY')

# Initialize object for sending messages to telegram
tg = TG(config('BOT_API_KEY', default=None))

# Retrieve ID of Telegram log channel
log_channel = config('LOG_ID', default=None)

# Create fernet object using secret key
fernet = Fernet(config('FERNET_KEY'))

DATABASE_CLASSES = {
    'codex_april_2019': CodexApril2019,
    'eh_july_2019': EHJuly2019,
    'cpp_workshop_may_2019': CPPWSMay2019,
    'rsc_2019': RSC2019,
    'c_cpp_workshop_august_2019': CCPPWSAugust2019,
    'do_hacktoberfest_2019': Hacktoberfest2019,
    'csi_november_2019': CSINovember2019,
    'csi_november_non_member_2019': CSINovemberNonMember2019,
    'p5_november_2019': P5November2019,
    'c_november_2019': CNovember2019,
    'bitgrit_december_2019': BitgritDecember2019,
    'test_users': TestTable,
    'users': Users,
    'events': Events,
    'codex_december_2019': CodexDecember2019,
    'bov_2020': BOV2020,
    'coursera_2020': Coursera2020,
    'tsg': TSG,
}

QR_BLACKLIST = (
    'paid',
    '_sa_instance_state',
)


def users_to_json(users: List[Users]) -> list:
    json_data = []
    for user in users:
        user_data = {}
        for k in user._db_field_map.keys():
            value = getattr(user, k)
            if value is not None and value != '':
                user_data[k] = value
        json_data.append(user_data)

    return json_data


def users_to_csv(table: DynamicDocument) -> str:
    keys = table._db_field_map.keys()
    ret = ','.join(keys) + '\n'
    for user in table.objects:
        for key in keys:
            ret += str(user[key]) + ','
        ret += '\n'
    return ret


def log(message: str):
    """Logs the given `message` to our Telegram logging channel"""
    try:
        app, version = request.headers.get('User-Agent').split('/')
        tg.send_message(log_channel, f'<b>Hades/{app}/{version}</b>: {message}')
    except ValueError:
        if request.headers.get('Origin') == 'https://charon.thescriptgroup.in':
            tg.send_message(log_channel, f'<b>Hades/Charon/1.0</b>: {message}')
        else:
            tg.send_message(log_channel, f'<b>Hades</b>: {message}')


def check_access(table_name: str) -> bool:
    """Returns whether or not the currently logged in user has access to `table_name`"""
    return Users.objects(access=table_name).first() is not None


def get_table_by_name(name: str) -> DynamicDocument:
    """Returns the database model class corresponding to the given name."""
    return DATABASE_CLASSES.get(name)


def get_table_full_name(name: str) -> str:
    """Returns the full name of the table"""
    return Events.objects(name=name).first().full_name


def get_accessible_tables():
    """Returns the list of tables the currently logged in user can access"""
    return Users.objects(username=current_user.username).first().access


def update_user(id_: int, table: DynamicDocument, user_data: dict) -> (bool, str):
    """
    :param id_ -> User ID
    :param table -> Table class
    :param user_data -> Dictionary containing fields to be updated
    :return: success/failure, reasoning
    """

    table_name = get_table_full_name(table.__tablename__)

    user = get_user(table, id_)
    if user is None:
        return False, f'No user with ID {id_}'

    log_message = (
        f'{current_user.name} updated the following for {user.name} in {table_name}:'
    )

    for k, v in user_data.items():
        o = getattr(user, k)
        if o != v:
            setattr(user, k, v)
            log_message += f'\nUpdated {k} of {user} from {o} to {v}'
        else:
            log_message += f'\n{k} of {user} is already {v}'

    log(log_message)

    success, reason = save_user(user)
    if not success:
        log(f'Could not update {id_} in {table_name} - {reason}')
        return success, reason
    return success, f'{user} has been successfully updated!'


def delete_user(id_: int, table_name: str) -> (bool, str):
    """
    :param id_ -> User ID
    :param table_name -> Name of the table user is to be deleted from
    :return success/failure, reasoning
    """

    table = get_table_by_name(table_name)

    if table is None:
        return False, f'Table {table_name} does not seem to exist!'

    user = table.objects(pk=id_)
    if user is None:
        return False, f'Table {table_name} does not have a user with ID {id_}'

    success, reason = delete_row_from_table(user)
    if not success:
        log(f'Could not delete user {user} - {reason}!')
        return success, f'Could not delete user {user} - {reason}!'
    log(
        f'User <code>{current_user.name}</code> has deleted <code>{user}</code> from <code>{table_name}</code>!'
    )
    return success, f'{current_user.name} has deleted {user} from {table_name}'


def get_current_id(table: DynamicDocument) -> int:
    """Function to return the latest ID based on the database entries. 1 if DB is empty."""
    try:
        id_ = table.objects().order_by('-id').first().id
    except:
        id_ = 0
    return int(id_) + 1


def generate_qr(user):
    """Function to generate and return a QR code based on the given data."""
    data = {k: v for k, v in user.__dict__.items() if k not in QR_BLACKLIST}
    data['table'] = user.__dict__.get('_cls', 'unknown_collection')
    return qrcode.make(base64.b64encode(dumps(data).encode()))


def send_mail(
    from_user: tuple, to: list, subject: str, content: str, attachments=None
) -> bool:
    if attachments is None:
        attachments = []

    # Bail out if SendGrid API key has not been set
    if SENDGRID_API_KEY is None:
        return False

    # Create a Content object
    html_content = Content('text/html', content)

    # Create a Mail object
    mail = Mail(from_user, to, subject, html_content)

    # Add attachments, if any
    for attachment in attachments:
        try:
            mail.add_attachment(
                Attachment(
                    attachment['data'], attachment['filename'], attachment['type']
                )
            )
        except KeyError:
            return False

    # Actually send the email
    try:
        SendGridAPIClient(SENDGRID_API_KEY).send(mail)
    except Exception as e:
        log('Exception occurred while sending mail!')
        log(e)
        return False
    return True


def encrypt(data: str) -> str:
    """
    Function to encrypt a string using Fernet (symmetric encryption)
    :param data: String to be encrypted
    :return: Encrypted string
    """
    return fernet.encrypt(data.encode()).decode('utf-8')


def decrypt(data: str) -> str:
    """
    Function to decrypt a string that was encrypted with Fernet
    :param data: String to be decrypted
    :return: Decrypted string
    """
    return fernet.decrypt(data.encode()).decode('utf-8')


def extract_timestamp(data: str) -> int:
    """
    Function to extract the timestamp from Fernet encrypted string
    :param data: The encrypted string
    :return: The timestamp at which it was created
    """
    return fernet.extract_timestamp(data.encode())
