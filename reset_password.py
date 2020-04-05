#!/usr/bin/env python3

from sys import exit
from getpass import getpass

from sqlalchemy.exc import IntegrityError

from hades import app, bcrypt, db
from hades.models.event import Events
from hades.models.user import Users
from hades.models.user_access import Access

username = input('Enter username: ')

user = db.session.query(Users).get(username)
if user is None:
    print(f'User {username} does not exist!')
    exit(1)

user.password = bcrypt.generate_password_hash(
    getpass(prompt='Enter new password: ')
).decode('utf-8')
try:
    db.session.commit()
except Exception as e:
    print('Exception occurred!')
    print(e)
    db.session.rollback()
