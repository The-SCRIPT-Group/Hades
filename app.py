#!/usr/bin/env python3
"""
Flask application to accept some details, generate, display, and email a QR code to users
"""

# pylint: disable=invalid-name,too-few-public-methods,no-member,line-too-long,too-many-locals

import base64
import os

import qrcode
import sendgrid
from sendgrid.helpers.mail import Attachment, Content, Email, Mail, Personalization

from flask import Flask, render_template, request
from sqlalchemy import exc
from flask_sqlalchemy import SQLAlchemy


FROM_EMAIL = os.getenv('FROM_EMAIL')
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')

app = Flask(__name__)
db = SQLAlchemy(app)
sg = sendgrid.SendGridAPIClient(SENDGRID_API_KEY)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')


DEPARTMENTS = {'cse': 'Computer Science and Engineering',
               'ece': 'Electronics and Communication Engineering',
               'mech': 'Mechanical Engineering',
               'civil': 'Civil Engineering',
               'chem': 'Chemical Engineering',
               'others': 'Others'}


@app.route('/submit_codex', methods=['POST'])
def submit_codex():
    return submit(CodexUsers, "CodeX", request.form)


@app.route('/submit_techo', methods=['POST'])
def submit_techo():
    return submit(TechoUsers, "Techo", request.form)


@app.route('/submit_workshop', methods=['POST'])
def submit_workshop():
    return submit(WorkshopUsers, "CPP Workshop", request.form)


def submit(table: db.Model, event_name: str, form_data):
    """
    Take data from the form, generate, display, and email QR code to user
    """

    for user in db.session.query(table).all():
        if form_data['email'] == user.email:
            return 'Email address {} already found in database!\
            Please re-enter the form correctly!'.format(form_data['email'])

        if str(form_data['phone_number']) == str(user.phone):
            return 'Phone number {} already found in database!\
            Please re-enter the form correctly!'.format(form_data['phone_number'])

    id = get_current_id(table)

    user = table(name=form_data['name'], email=form_data['email'],
                 phone=form_data['phone_number'], id=id)

    if form_data['department']:
        user.department = form_data['department']

    try:
        db.session.add(user)
        db.session.commit()
    except exc.IntegrityError:
        return "Error occurred trying to enter values into the database!"

    img = generate_qr(form_data, id)
    img.save('qr.png')
    img_data = open('qr.png', 'rb').read()
    encoded = base64.b64encode(img_data).decode()

    name = form_data['name']
    from_email = Email(FROM_EMAIL)
    to_email = Email(form_data['email'])
    p = None
    if form_data['email_second_person'] and form_data['name_second_person']:
        cc_email = Email(form_data['email_second_person'])
        name += ', {}'.format(form_data['name_second_person'])
        p = Personalization()
        p.add_to(cc_email)

    subject = 'Registration for {} April 2019 - ID {}'.format(event_name, id)
    message = """<img src='https://drive.google.com/uc?id=12VCUzNvU53f_mR7Hbumrc6N66rCQO5r-&export=download'>
    <hr>
    {}, your registration is done!
    <br/>
    A QR code has been attached below!
    <br/>
    You're <b>required</b> to present this on the day of the event.
    """.format(name)
    content = Content('text/html', message)
    mail = Mail(from_email, subject, to_email, content)
    if p:
        mail.add_personalization(p)

    attachment = Attachment()
    attachment.type = 'image/png'
    attachment.filename = 'qr.png'
    attachment.content = encoded

    mail.add_attachment(attachment)

    response = sg.client.mail.send.post(request_body=mail.get())
    print(response.status_code)
    print(response.body)
    print(response.headers)

    return 'Please save this QR Code. It has also been emailed to you.<br><img src=\
            "data:image/png;base64, {}"/>'.format(encoded)


@app.route('/codex')
def codex():
    return render_template('form.html', event='CodeX', group=True, submit='submit_codex', department_generic=True)


@app.route('/techo')
def techo():
    return render_template('form.html', event='Techo', group=False, submit='submit_techo', department_generic=True)


@app.route('/users', methods=['GET', 'POST'])
def display_users():
    """
    Display the list of users, after authentication
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == os.getenv('USERNAME'):
            if password == os.getenv('PASSWORD'):
                return render_template('users.html', users=db.session.query(request.form['table']).all())
            return 'Invalid password!'
        return 'Invalid user!'
    return '''
            <form action="" method="post">
                <p><input type=text name=username required>
                <p><input type=password name=password required>
                <p><input type=submit value=Login>
                <select name="table" id="table">
                    <option value="codex_users" selected>CodeX</option>
                    <option value="techo_users">Techo</option>
                    <option value="workshop_users">CPP Workshop</option>
                </select>                
            </form>
            '''


@app.route('/')
def root():
    """
    Main endpoint. Display the form to the user.
    """
    return render_template('form.html', event='CPP Workshop', group=False, submit='submit_workshop', department_generic=False)


def get_current_id(table: db.Model):
    """
    Function to return the latest ID
    """
    try:
        id = db.session.query(table).all()[-1].id
    except IndexError:
        id = 0
    return int(id) + 1


def generate_qr(form_data, id):
    """
    Function to generate and return a QR code based on the given data
    """
    return qrcode.make("\nName: {}\nEmail: {}\nID: {}\nPhone Number: {}"
                       .format(form_data['name'], form_data['email'],
                               id, form_data['phone_number']))


class CodexUsers(db.Model):
    """
    Database model class
    """
    __tablename__ = 'codex_users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(50), unique=True)
    phone = db.Column(db.BigInteger, unique=True)
    department = db.Column(db.String(50))

    def __repr__(self):
        return '%r' % [self.id, self.name, self.email, self.phone, self.department]


class TechoUsers(db.Model):
    """
    Database model class
    """
    __tablename__ = 'techo_users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(50), unique=True)
    phone = db.Column(db.BigInteger, unique=True)
    department = db.Column(db.String(50))

    def __repr__(self):
        return '%r' % [self.id, self.name, self.email, self.phone, self.department]


class WorkshopUsers(db.Model):
    """
    Database model class
    """
    __tablename__ = 'workshop_users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(50), unique=True)
    phone = db.Column(db.BigInteger, unique=True)

    def __repr__(self):
        return '%r' % [self.id, self.name, self.email, self.phone]


if __name__ == '__main__':
    app.run()
