import base64
from flask import Flask, request
import sendgrid
import qrcode

app = Flask(__name__)

from sendgrid.helpers.mail import *


@app.route('/submit', methods=['POST'])
def stuff():
    name = request.form['name']
    email = request.form['email']
    roll_number = request.form['roll_number']
    img = qrcode.make("Name: {}\nEmail: {}\nRoll Number: {}\n".format(name, email, roll_number))
    img.save('qr.png')
    img_data = open('qr.png', 'rb').read()
    encoded = base64.b64encode(img_data).decode()

    sg = sendgrid.SendGridAPIClient(apikey=os.getenv('SENDGRID_API_KEY', None))

    from_email = Email('script.mailus@gmail.com')
    to_email = Email(email)
    subject = 'Registration for {}'.format(roll_number)
    content = Content('text/plain', 'QR code attached below!')
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

    return 'Please save this QR Code. It has also been emailed to you.<br><img src="data:image/jpeg;base64, {}"/>'.format(encoded)

@app.route('/')
def root():
    with open('form.html', 'r') as file:
        data = file.read()
    return data

if __name__ == '__main__':
    app.run()