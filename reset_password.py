#!/usr/bin/env python3

from sys import exit
from getpass import getpass

from hades.models.user import Users

username = input('Enter username: ')

user = Users.query.get(username)
if user is None:
    print(f'User {username} does not exist!')
    exit(1)

user.generate_password_hash(getpass(prompt='Enter new password: '))
try:
    Users.query.session.commit()
except Exception as e:
    print('Exception occurred!')
    print(e)
    Users.query.session.rollback()
