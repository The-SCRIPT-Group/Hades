from json import dumps

from hades import db


def validate(data, table):
    # Ensure nobody else in the table has the same email address
    if db.session.query(table).filter(table.email == data.email).first():
        return f'Email address {data.email} already found in database! Please re-enter the form correctly!'

    # Ensure nobody else int he table has the same phone number
    for num in data.phone.split('|'):
        if db.session.query(table).filter(table.phone.like(f'%{num}%')).first():
            return f'Phone number {num} already found in database! Please re-enter the form correctly!'

    return True


def users_to_json(users):
    json_data = []
    for user in users:
        user_data = {}
        for k, v in user.__dict__.items():
            if k == '_sa_instance_state':
                continue
            user_data[k] = v
        json_data.append(user_data)

    return dumps(json_data)
