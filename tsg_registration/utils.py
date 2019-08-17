from tsg_registration import db


def validate(data, table):
    for user in db.session.query(table).all():
        if data.email == user.email:
            return "Email address {} already found in database!\
            Please re-enter the form correctly!".format(
                data.email
            )

        input_phone = data.phone.split('|')[0]
        user_phone = user.phone.split('|')[0]

        if input_phone == user_phone:
            return "Phone number {} already found in database!\
                Please re-enter the form correctly!".format(
                input_phone
            )

    return True
