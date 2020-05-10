import base64
import os
from json import dumps
from typing import Union
from urllib.parse import urlparse, urljoin

import qrcode
from flask import request
from flask_login import current_user
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError

from hades import db
from hades.models.codex import CodexApril2019, RSC2019, CodexDecember2019, BOV2020
from hades.models.csi import CSINovember2019, CSINovemberNonMember2019
from hades.models.event import Events
from hades.models.giveaway import Coursera2020
from hades.models.techo import EHJuly2019, P5November2019
from hades.models.test import TestTable
from hades.models.user import Users, TSG
from hades.models.user_access import Access
from hades.models.workshop import (
    CPPWSMay2019,
    CCPPWSAugust2019,
    Hacktoberfest2019,
    CNovember2019,
    BitgritDecember2019,
)
from hades.telegram import TG

# Initialize object for sending messages to telegram
tg = TG(os.getenv('BOT_API_KEY'))

# Retrieve ID of Telegram log channel
log_channel = os.getenv('LOG_ID')

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
    'access': Access,
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


def users_to_json(users: list) -> str:
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


def get_current_id(table: db.Model) -> int:
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
