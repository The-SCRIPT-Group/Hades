#!/usr/bin/env python3

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from hades import app

# TODO: Let this actually work

# Source is taken from app
src = input('Enter source DB URI: ')
dest = input('Enter destination DB URI: ')

dest_app = Flask(__name__)
dest_db = SQLAlchemy(dest_app)
dest_app.config['SQLALCHEMY_DATABASE_URI'] = dest


app.config['SQLALCHEMY_DATABASE_URI'] = src
print('Source tables: ')
print(db.engine.table_names())
print('Running create_all() on destination URI')
app.config['SQLALCHEMY_DATABASE_URI'] = dest
db.create_all()
print(db.engine.table_names())
app.config['SQLALCHEMY_DATABASE_URI'] = src


tables = db.engine.table_names()
tables.reverse()
for table in tables:
    print(f'Checking entries in {table}')
    table = EVENT_CLASSES[table]
    if table is None:
        print('Table is None')
        continue
    data = db.session.query(table).all()
    for i in data:
        user_data = table()
        for k, v in i.__dict__.items():
            if k == '_sa_instance_state':
                continue
            setattr(user_data, k, v)
        dest_db.session.add(user_data)
    dest_db.session.commit()
