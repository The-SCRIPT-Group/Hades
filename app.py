#!/usr/bin/env python3
"""
Flask application to accept some details, generate, display, and email a QR code to users
"""

# pylint: disable=invalid-name,too-few-public-methods,no-member

import base64
import os

import qrcode
import sendgrid
from sendgrid.helpers.mail import Attachment, Content, Email, Mail

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy


FROM_EMAIL = os.getenv('FROM_EMAIL', None)
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', None)

app = Flask(__name__, static_url_path='')
sg = sendgrid.SendGridAPIClient(apikey=SENDGRID_API_KEY)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', None)

db = SQLAlchemy(app)

DEPARTMENTS = {'cse': 'Computer Science and Engineering',
               'ece': 'Electronics and Communication Engineering',
               'mech': 'Mechanical Engineering',
               'civil': 'Civil Engineering',
               'chem': 'Chemical Engineering'}


class User(db.Model):
    """
    Database model class
    """
    __tablename__ = 'users'
    techo_id = db.Column(db.Integer, primary_key=True)
    roll_number = db.Column(db.Integer, unique=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(50), unique=True)
    phone = db.Column(db.Integer, unique=True)
    department = db.Column(db.String(50))
    year = db.Column(db.Integer)

    def __repr__(self):
        pass


@app.route('/submit', methods=['POST'])
def stuff():
    """
    Accept data from the form, generate, display, and email QR code to user
    """
    techo_id = get_current_id()
    img = generate_qr(request.form, techo_id)
    img.save('qr.png')
    img_data = open('qr.png', 'rb').read()
    encoded = base64.b64encode(img_data).decode()

    from_email = Email(FROM_EMAIL)
    to_email = Email(request.form['email'])
    subject = 'Registration for TECHO-{}'.format(techo_id)
    content = Content('text/plain', 'QR code has been attached below! You\'re required to present\
            this on the day of the event.')
    mail = Mail(from_email, subject, to_email, content)

    attachment = Attachment()
    attachment.type = 'image/png'
    attachment.filename = 'qr.png'
    attachment.content = encoded

    mail.add_attachment(attachment)

    response = sg.client.mail.send.post(request_body=mail.get())
    print(response.status_code)
    print(response.body)
    print(response.headers)

    user = User(roll_number=request.form['roll_number'], name=request.form['name'],
                email=request.form['email'], phone=request.form['phone'],
                department=DEPARTMENTS[request.form['department']], year=request.form['year'])
    db.session.add(user)
    db.session.commit()

    return 'Please save this QR Code. It has also been emailed to you.<br><img src=\
            "data:image/png;base64, {}"/>'.format(encoded)


@app.route('/')
def root():
    """
    Main endpoint. Display the form to the user.
    """
    return app.send_static_file('form.html')


def get_current_id():
    """
    Function to return the latest ID
    """
    # Just a stub for now
    # TODO - Check database and return newest unused ID
    return '001'


def generate_qr(form_data, techo_id):
    """
    Function to generate and return a QR code based on the given data
    """
    return qrcode.make("\nName: {}\nEmail: {}\nRoll Number: {}\nID: {}\nPhone Number: {}\n\
            Department: {}\nYear: {}".format(form_data['name'], form_data['email'],
                                             form_data['roll_number'], techo_id,
                                             form_data['phone_number'],
                                             DEPARTMENTS[form_data['department']],
                                             form_data['year']))


if __name__ == '__main__':
    app.run()
