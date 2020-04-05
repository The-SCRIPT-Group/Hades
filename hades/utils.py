from json import dumps

from hades import db


def validate(data, table):
    for user in db.session.query(table).all():
        if data.email == user.email:
            return 'Email address {} already found in database!\
            Please re-enter the form correctly!'.format(
                data.email
            )

        input_phone = data.phone.split('|')[0]
        user_phone = user.phone.split('|')[0]

        if input_phone == user_phone and input_phone != '':
            return 'Phone number {} already found in database!\
                Please re-enter the form correctly!'.format(
                input_phone
            )

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
