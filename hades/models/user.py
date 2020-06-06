from random import choice
from string import ascii_letters, digits, punctuation

from flask_bcrypt import Bcrypt
from flask_login import UserMixin

from hades import app, db

bcrypt = Bcrypt(app)


class Users(db.Model, UserMixin):
    """
    Database model class
    """

    __tablename__ = 'users'
    name = db.Column(db.String(30))
    username = db.Column(db.String(20), primary_key=True)
    password = db.Column(db.String(100))
    api_key = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(50), unique=True)

    def get_id(self):
        return self.username if self is not None else None

    def check_password_hash(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password, password)

    def check_api_key(self, api_key: str) -> bool:
        return bcrypt.check_password_hash(self.api_key, api_key)

    def generate_password_hash(self, password: str):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def generate_api_key(self) -> str:
        api_key = ''.join(
            choice(ascii_letters + digits + punctuation) for _ in range(32)
        )
        self.api_key = bcrypt.generate_password_hash(api_key).decode('utf-8')
        return api_key

    def __repr__(self):
        return '%r' % [self.username, self.name, self.email]


class TSG(db.Model):
    """
    Database model class
    """

    __tablename__ = 'tsg'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(50), unique=True)
    phone = db.Column(db.String(10), unique=True)

    def __repr__(self):
        return '%r' % [self.id, self.name, self.email, self.phone]
