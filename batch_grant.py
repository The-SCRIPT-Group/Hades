#!/usr/bin/env python3

from sys import exit

from sqlalchemy.exc import IntegrityError

from hades import db
from hades.models.user import Users
from hades.models.user_access import Access

tables = db.engine.table_names()
print(tables)
table = input(f"Enter table name: ")
if table not in tables:
    print(f"Table {table} does not exist!")
    exit(1)

print("Keep entering usernames, ctrl c/d to exit!")
users = []
try:
    while True:
        username = input("Enter username: ")
        user = db.session.query(Users).get(username)
        if user is None:
            print(f"User {username} does not seem to exist!")
            exit(1)
        users.append(user)
except EOFError:
    pass
except KeyboardInterrupt:
    pass

for user in users:
    username = user.username
    access = Access(event=table, user=username)
    db.session.add(access)
    try:
        db.session.commit()
    except IntegrityError:
        print(f"User {username} already seems to have access to {table}!")
        db.session.rollback()
        continue
    print(f"Granted access on {table} to {username}")
