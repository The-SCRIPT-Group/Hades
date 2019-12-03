#!/usr/bin/env python3

from sys import stdin, stdout, exit

from sqlalchemy.exc import IntegrityError

from tsg_registration import db
from tsg_registration.models.event import Events
from tsg_registration.models.user import Users
from tsg_registration.models.user_access import Access


tables = db.engine.table_names()
username = input(f"Enter username that needs access to all tables: ")
user = db.session.query(Users).get(username)
if user is None:
    print(f"User {username} does not seem to exist!")
    exit(1)

for table in tables:
    access = Access(event=table, user=username)
    db.session.add(access)
    try:
        db.session.commit()
    except IntegrityError:
        print(f"User {username} already seems to have access to {table}!")
        db.session.rollback()
        continue
    print(f"Granted access on {table} to {username}")
