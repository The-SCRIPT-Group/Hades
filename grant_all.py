#!/usr/bin/env python3

from sys import stdin, stdout, exit

from sqlalchemy.exc import IntegrityError

from hades import db
from hades.models.user import Users
from hades.models.user_access import Access


tables = db.engine.table_names()
username = input(f'Enter username that needs access to all tables: ')
user = Users.query.get(username)
if user is None:
    print(f'User {username} does not seem to exist!')
    exit(1)

for table in tables:
    access = Access(event=table, user=username)
    db.session.add(access)
    try:
        db.session.commit()
    except IntegrityError:
        print(f'User {username} already seems to have access to {table}!')
        db.session.rollback()
        continue
    print(f'Granted access on {table} to {username}')
