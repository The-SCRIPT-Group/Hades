from tsg_registration import db


def validate(data, table):
    for user in db.session.query(table).all():
        if data.email == user.email:
            return "Email address {} already found in database!\
            Please re-enter the form correctly!".format(
                data.email
            )

        if data.phone in user.phone:
            return "Phone number {} already found in database!\
                Please re-enter the form correctly!".format(
                data.phone
            )
    return True
