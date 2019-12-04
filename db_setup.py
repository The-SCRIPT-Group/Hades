#!/usr/bin/env python3

from hades import db
from hades.models.event import Events

db.create_all()

for table in db.engine.table_names():
    current_event = db.session.query(Events).get(table)
    if current_event is None:
        full_name = input(f"Enter full name for table {table}: ")
        new_event = Events(name=table, full_name=full_name)
        db.session.add(new_event)
        db.session.commit()
        print(f"Added event {table} with full name {full_name}")
    else:
        print(f"Found table {current_event.name} - {current_event.full_name}")
