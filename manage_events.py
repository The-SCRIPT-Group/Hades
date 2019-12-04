#!/usr/bin/env python3

from sys import stdin, stdout, exit

from hades import db
from hades.models.event import Events


def send_help():
    print("Enter to continue, d to delete, e to edit, h for help, Ctrl C/D to exit")


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
        elif ch == "d":
            db.session.delete(current_event)
            db.session.commit()
            print(f"Deleted {table}")
        elif ch == "e":
            current_event.full_name = input(f"Enter full name for table {table}: ")
            db.session.commit()
            print(f"Updated {table} full name to {current_event.full_name}")
except EOFError:
    print("Exiting!")
except KeyboardInterrupt:
    print("Exiting!")
except IndexError:
    print("No such table, exiting!")
except ValueError:
    print("Exiting!")
