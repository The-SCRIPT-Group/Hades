from json import dumps, loads

from flask import jsonify, request
from flask_login import login_required, current_user
from sendgrid import Content, Mail, SendGridAPIClient
from sqlalchemy.exc import IntegrityError

from hades import (
    app,
    log,
    get_accessible_tables,
    db,
    get_table_by_name,
    FROM_EMAIL,
    SENDGRID_API_KEY,
)
from hades.utils import check_access, delete_user, DATABASE_CLASSES, users_to_json


@app.route('/api/authenticate', methods=['POST'])
@login_required
def authenticate_api():
    """Used to authenticate a login from an external application"""
    return (
        jsonify({'message': f'Successfully authenticated as {current_user.username}'}),
        200,
    )


@app.route('/api/events')
@login_required
def events_api():
    """Returns a JSON consisting of the tables the user has the permission to view"""
    ret = {}
    log(f'<code>{current_user.name}</code> is accessing the list of events!</code>')
    for table in get_accessible_tables():
        if table.name not in ('access', 'events', 'users',):
            ret[table.name] = table.full_name
    return jsonify(ret), 200


@app.route('/api/stats')
@login_required
def stats_api():
    """Returns a JSON consisting of the tables the user has the permission to view and the users registered per table"""
    ret = {}
    log(f'<code>{current_user.name}</code> is accessing the stats of events!</code>')
    for table in get_accessible_tables():
        if table.name not in ('access', 'events', 'test_users', 'tsg', 'users',):
            ret[table.full_name] = len(
                db.session.query(DATABASE_CLASSES[table.name]).all()
            )
    return jsonify(ret), 200


@app.route('/api/users')
@login_required
def users_api():
    """Returns a JSON consisting of the users in the given table"""
    table_name = request.args.get('table')
    if not table_name:
        return jsonify({'response': 'Please provide all required data'}), 400

    if table_name == 'all':
        tables = get_accessible_tables()
        users = set()
        for table in tables:
            if table.name in ('access', 'events', 'users'):
                continue
            table_users = db.session.query(get_table_by_name(table.name)).all()
            for user in table_users:
                phone = (
                    user.phone.split('|')[1]
                    if len(user.phone.split('|')) == 2
                    else user.phone
                )
                if ',' in user.name:
                    continue
                name = user.name.split(' ')[0].title()
                users.add(dumps({'name': name, 'phone': phone}))
        final_users = []
        for user in users:
            final_users.append(loads(user))
        return dumps(final_users)

    access = check_access(table_name)
    if access is None:
        return jsonify({'response': 'Unauthorized'}), 401
    table = get_table_by_name(table_name)
    if table is None:
        return jsonify({'response': f'Table {table_name} does not exist!'}), 400
    return users_to_json(db.session.query(table).all()), 200


@app.route('/api/create', methods=['POST'])
@login_required
def create():
    """Creates a user as specified in the request data"""

    if 'table' in request.form:
        table_name = request.form['table']
    else:
        return jsonify({'response': 'Please provide the table name!'}, 400)

    table = get_table_by_name(table_name)
    if table is None:
        return jsonify({'response': f'Table {table_name} does not seem to exist!'}, 400)

    access = check_access(table_name)
    if access is None:
        return jsonify({'response': 'Unauthorized'}), 401

    user_data = {}

    for k, v in request.form.items():
        if k == 'table':
            continue
        user_data[k] = v

    try:
        user = table(**user_data)
    except Exception as e:
        log(
            f'Exception occurred when <code>{current_user.name} tried to create user with {user_data} in {table_name}'
        )
        log(e)
        return jsonify({'response': 'Exception occurred trying to create user'}), 400

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        return (
            jsonify(
                {
                    'response': 'Integrity constraint violated, please re-check your data!'
                }
            ),
            400,
        )
    log(
        f'User <code>{user}</code> has been created in table <code>{table_name}</code>!',
    )
    return jsonify({'response': f'Created user {user} successfully!'}), 200


@app.route('/api/delete', methods=['DELETE'])
@login_required
def delete():
    """Deletes the user as specified in the request data"""

    # Ensure user has passed `table` and `id`
    if 'table' in request.form and 'id' in request.form:
        table_name = request.form['table']
        id = request.form['id']
    else:
        return jsonify({'response': 'Please provide all required data'}), 400

    # Confirm that the user has access to the desired table
    access = check_access(table_name)
    if access is None:
        return (
            jsonify({'response': f'You are not authorized to access {table_name}'}),
            401,
        )

    table = get_table_by_name(table_name)
    if table is None:
        return jsonify({'response': f'{table_name} does not seem to exist!'}), 400

    # Let us delete all entries, if so required
    if id == 'all':
        # Store the message to be returned
        ret = []
        for user in db.session.query(table).all():
            if delete_user(user.id, table_name):
                ret.append(f'Deleted user {user} from {table_name}')
            else:
                ret.append(f'Failed to delete user {user} from {table_name}')
        return jsonify({'response': ret})

    # If just a specific ID is to be deleted
    if delete_user(id, table_name):
        return jsonify({'response': f'Deleted user with id {id} from {table_name}'})
    return jsonify(
        {'response': f'Failed to delete user with id {id} from {table_name}'}
    )


@app.route('/api/update', methods=['PUT'])
@login_required
def update_user():
    """
    Updates a user as specified in the request data

    Fields required

    -> table - The name of the table
    -> key - The name of the attribute used to identify the user, for example `id`
    -> data - The value of the identifier
    -> Rest of the parameters will be the attributes to be updated
    """
    if (
        'table' in request.form
        and 'key' in request.form
        and request.form['key'] in request.form
    ):
        table_name = request.form['table']
        key = request.form['key']
        data = request.form[key]
    else:
        return jsonify({'response': 'Please provide all required data'}), 400

    access = check_access(table_name)
    if access is None:
        return jsonify({'response': 'Unauthorized'}), 401

    table = get_table_by_name(table_name)
    if table is None:
        return jsonify({'response': 'Please provide a valid table name'}), 400

    user = db.session.query(table).get(data)

    for k, v in request.form.items():
        if k in ('key', 'table', key):
            continue
        if getattr(user, k) != v:
            setattr(user, k, v)
            print(f'Updated {k} of {user} to {v}')
    try:
        db.session.commit()
    except IntegrityError:
        return (
            jsonify(
                {
                    'response': 'Integrity constraint violated, please re-check your data!'
                }
            ),
            400,
        )
    log(
        f'User <code>{current_user.name}</code> has updated <code>{user}</code> in <code>{table_name}</code>!',
    )
    return jsonify({'response': f'Updated user {user}'}), 200


@app.route('/api/sendmail', methods=['POST'])
@login_required
def send_mail():
    """Sends a mail to users as specified in the request data"""
    for field in ('content', 'subject', 'table', 'ids'):
        if field not in request.form:
            return jsonify({'response': 'Please provide all required data'}), 400

    subject = request.form['subject']
    table_name = request.form['table']

    if table_name in ('access', 'events', 'users'):
        return jsonify({'response': 'Seriously?'}), 400
    access = check_access(table_name)
    if access is None:
        return jsonify({'response': 'Unauthorized'}), 401

    table = get_table_by_name(table_name)
    if 'ids' in request.form and request.form['ids'] != 'all':
        ids = list(map(lambda x: int(x), request.form['ids'].split(' ')))
        users = db.session.query(table).filter(table.id.in_(ids)).all()
    else:
        users = db.session.query(table).all()

    if 'email_address' in request.form:
        email_address = request.form['email_address']
    else:
        email_address = FROM_EMAIL

    for user in users:
        if 'formattable_content' in request.form and 'content_fields' in request.form:
            d = {}
            for f in request.form['content_fields'].split(','):
                d[f] = getattr(user, f)
            content = request.form['content']
            content += request.form['formattable_content'].format(**d)

        else:
            content = "<img src='https://drive.google.com/uc?id=12VCUzNvU53f_mR7Hbumrc6N66rCQO5r-&export=download' style='width:30%;height:50%'><hr><br> <b>Hey there!</b><br><br>" + str(
                request.form['content']
            ).replace(
                '\n', '<br/>'
            )

        mail_content = Content('text/html', content)
        if ',' in user.name:
            mail = Mail(FROM_EMAIL, email_address, subject, mail_content)
            mail.add_cc((user.email.split(',')[0], user.name.split(',')[0]))
            mail.add_cc(
                (user.email.split(',')[1].rstrip(), user.name.split(',')[1].rstrip())
            )
        else:
            mail = Mail(FROM_EMAIL, (user.email, user.name), subject, mail_content)
        try:
            SendGridAPIClient(SENDGRID_API_KEY).send(mail)
        except Exception as e:
            print(e)
            return jsonify({'response': f'Failed to send mail to {user}'}), 500

    log(
        f'User <code>{current_user.name}</code> has sent mails with subject <code>{subject}</code> to <code>{table_name}</code>!',
    )
    return jsonify({'response': 'Sent mail'}), 200
