from json import dumps, loads

from decouple import config
from flask import jsonify, request
from flask_login import login_required, current_user

from . import (
    app,
    log,
)
from .db_utils import insert, get_user, save_user
from .utils import (
    check_access,
    delete_user,
    users_to_json,
    send_mail,
    get_table_full_name,
    get_accessible_tables,
    get_table_by_name,
    users_to_csv,
)


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
    log(f'<code>{current_user.name}</code> is accessing the list of events!')
    for table in get_accessible_tables():
        if table.name not in (
            'access',
            'events',
            'users',
        ):
            ret[table.name] = table.full_name
    return jsonify(ret), 200


@app.route('/api/stats')
@login_required
def stats_api():
    """Returns a JSON consisting of the tables the user has the permission to view and the users registered per table"""
    log(f'<code>{current_user.name}</code> is accessing the stats of events!')
    if 'table' in request.args:
        table_name = request.args.get('table')
        table = get_table_by_name(table_name)
        if table is None:
            return jsonify({'message': f'Table {table_name} does not exist'}), 400
        if check_access(table_name):
            return (
                jsonify({get_table_full_name(table_name): len(table.objects)}),
                200,
            )
        return (
            jsonify({'message': f'You do not have access to table {table}'}),
            403,
        )
    ret = {}
    for table in get_accessible_tables():
        if table.name not in (
            'access',
            'events',
            'test_users',
            'tsg',
            'users',
        ):
            ret[table.full_name] = len(get_table_by_name(table.name).objects())
    return jsonify(ret), 200


@app.route('/api/users')
@login_required
def users_api():
    """Returns a JSON consisting of the users in the given table"""
    table_name = request.args.get('table')
    if not table_name:
        return jsonify({'message': 'Please provide all required data'}), 400

    if table_name == 'all':
        log(
            f'<code>{current_user.name}</code> is accessing all tables that they have access to!'
        )
        tables = get_accessible_tables()
        users = set()
        for table in tables:
            if table.name in ('access', 'events', 'users'):
                continue
            table_users = get_table_by_name(table.name).objects()
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
        return jsonify(dumps(final_users)), 200

    log(f'<code>{current_user.name}</code> is accessing table {table_name}!')
    access = check_access(table_name)
    if access is None:
        return jsonify({'message': 'Unauthorized'}), 401
    table = get_table_by_name(table_name)
    if table is None:
        return jsonify({'message': f'Table {table_name} does not exist!'}), 400
    if request.args.get('csv'):
        return users_to_csv(table), 200
    return jsonify(users_to_json(table.objects())), 200


@app.route('/api/create', methods=['POST'])
@login_required
def create():
    """Creates a user as specified in the request data"""
    if 'table' in request.form:
        table_name = request.form['table']
    else:
        return jsonify({'message': 'Please provide the table name!'}, 400)

    table = get_table_by_name(table_name)
    if table is None:
        return jsonify({'message': f'Table {table_name} does not seem to exist!'}, 400)

    access = check_access(table_name)
    if access is None:
        return jsonify({'message': 'Unauthorized'}), 401

    log(
        f'<code>{current_user.name}</code> is trying to add a user to table {table_name}!'
    )

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
        return jsonify({'message': 'Exception occurred trying to create user'}), 400

    success, reason = insert([user])

    if not success:
        return (
            jsonify({'message': f'Error occurred, {reason}'}),
            400,
        )
    log(
        f'User <code>{user}</code> has been created in table <code>{table_name}</code>!',
    )
    return jsonify({'message': f'Created user {user} successfully!'}), 200


@app.route('/api/delete', methods=['DELETE'])
@login_required
def delete_api():
    """Deletes the user as specified in the request data"""

    # TODO: use utils.delete_user()
    # Ensure user has passed `table` and `id`
    if 'table' in request.form and 'id' in request.form:
        table_name = request.form['table']
        id_ = request.form['id']
    else:
        return jsonify({'message': 'Please provide all required data'}), 400

    # Confirm that the user has access to the desired table
    access = check_access(table_name)
    if access is None:
        return (
            jsonify({'message': f'You are not authorized to access {table_name}'}),
            401,
        )

    table = get_table_by_name(table_name)
    if table is None:
        return jsonify({'message': f'{table_name} does not seem to exist!'}), 400

    # Let us delete all entries, if so required
    if id_ == 'all':
        log(
            f'<code>{current_user.name}</code> is trying to delete all entries from table {table_name}!'
        )
        # Store the message to be returned
        ret = []
        for user in table.objects():
            if delete_user(user.id, table_name):
                ret.append(f'Deleted user {user} from {table_name}')
            else:
                ret.append(f'Failed to delete user {user} from {table_name}')
        return jsonify({'message': ret})

    log(
        f'<code>{current_user.name}</code> is trying to delete ID {id_} from table {table_name}!'
    )
    # If just a specific ID is to be deleted
    if delete_user(id_, table_name):
        return jsonify({'message': f'Deleted user with id {id_} from {table_name}'})
    return jsonify(
        {'message': f'Failed to delete user with id {id_} from {table_name}'}
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

    # TODO: use utils.update_user()

    if (
        'table' in request.form
        and 'key' in request.form
        and request.form['key'] in request.form
    ):
        table_name = request.form['table']
        key = request.form['key']
        data = request.form[key]
    else:
        return jsonify({'message': 'Please provide all required data'}), 400

    access = check_access(table_name)
    if access is None:
        return jsonify({'message': 'Unauthorized'}), 401

    table = get_table_by_name(table_name)
    if table is None:
        return jsonify({'message': 'Please provide a valid table name'}), 400

    log(
        f'<code>{current_user.name}</code> is trying to update user {key} {data} in table {table_name}!'
    )

    user = get_user(table, data)

    log_message = f'{current_user.name} has:'
    for k, v in request.form.items():
        if k in ('key', 'table', key):
            continue
        o = getattr(user, k)
        if o != v:
            setattr(user, k, v)
            log_message += f'\nUpdated {k} of {user.name} from {o} to {v}'

    log(log_message)
    success, reason = save_user(user)
    if not success:
        return (
            jsonify({'message': f'Error occurred - {reason}'}),
            400,
        )
    log(
        f'User <code>{current_user.name}</code> has updated <code>{user}</code> in <code>{table_name}</code>!',
    )
    return jsonify({'message': f'Updated user {user}'}), 200


@app.route('/api/sendmail', methods=['POST'])
@login_required
def sendmail():
    """Sends a mail to users as specified in the request data"""
    for field in ('content', 'subject', 'table', 'ids'):
        if field not in request.form:
            return jsonify({'message': 'Please provide all required data'}), 400

    subject = request.form['subject']
    table_name = request.form['table']

    if table_name in ('access', 'events', 'users'):
        return jsonify({'message': 'Seriously?'}), 400
    access = check_access(table_name)
    if access is None:
        return jsonify({'message': 'Unauthorized'}), 401

    log(f'<code>{current_user.name}</code> is send a mail to table {table_name}!')

    table = get_table_by_name(table_name)
    if 'ids' in request.form and request.form['ids'] != 'all':
        ids = list(map(lambda x: int(x), request.form['ids'].split(' ')))
        users = table.objects(pk__in=ids)
    else:
        users = table.objects()

    if 'email_address' in request.form:
        email_address = request.form['email_address']
    else:
        email_address = config('FROM_EMAIL', default='noreply@thescriptgroup.in')

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

        to_emails = []
        if ',' in user.name:
            to_emails.append((user.email.split(',')[0], user.name.split(',')[0]))
            to_emails.append(
                (user.email.split(',')[1].rstrip(), user.name.split(',')[1].rstrip())
            )
        else:
            to_emails.append((user.email, user.name))

        if not send_mail(email_address, to_emails, subject, content):
            return jsonify({'message': f'Failed to send mail to {user}'}), 500

    log(
        f'User <code>{current_user.name}</code> has sent mails with subject <code>{subject}</code> to <code>{table_name}</code>!',
    )
    return jsonify({'message': 'Sent mail'}), 200
