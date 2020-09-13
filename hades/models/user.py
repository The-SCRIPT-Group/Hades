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
    email = db.Column(db.String(50), unique=True)

    def get_id(self):
        return self.username if self is not None else None

    def check_password_hash(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password, password)

    def generate_password_hash(self, password: str):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

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
