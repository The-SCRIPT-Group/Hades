#!/usr/bin/env python3

from sys import stdin, stdout, exit

from sqlalchemy.exc import IntegrityError

from tsg_registration import db
from tsg_registration.models.event import Events
from tsg_registration.models.user import Users
from tsg_registration.models.user_access import Access


def send_help():
    print(
        "Enter to continue, g to grant access to a user, h for help, Ctrl C/D to exit"
    )


tables = db.engine.table_names()
for i in range(len(tables)):
    table = tables[i]
    current_event = db.session.query(Events).get(table)
    if current_event is None:
        print("Please run `db_setup.py` prior to using this!")
        exit(1)
    else:
        print(f"{i + 1}. {current_event.name} - {current_event.full_name}")

try:
    while True:
        ch = int(
            input(
                "Enter the number of the table you wish to interact with, enter/Ctrl C/D to exit\ntable: "
            )
        )
        table = tables[ch - 1]
        send_help()
        current_event = db.session.query(Events).get(table)
        stdout.write(f"{table} -> ")
        stdout.flush()
        ch = stdin.read(1)
        if ch == "h":
            send_help()
        elif ch == "g":
            username = input(f"Enter username that needs access to {table}: ")
            user = db.session.query(Users).get(username)
            if user is None:
                print(f"User {username} does not seem to exist!")
                break
            access = Access(event=table, user=username)
            try:
                db.session.add(access)
                db.session.commit()
            except IntegrityError:
                print("IntegrityError, what did you do!")
                break
            print(f"Grant access on {table} to {username}")
except EOFError:
    print("Exiting!")
except KeyboardInterrupt:
    print("Exiting!")
except IndexError:
    print("No such table, exiting!")
except ValueError:
    print("Exiting!")
