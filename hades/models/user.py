from flask_login import UserMixin

from hades import db
from hades.utils import validate


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

    def validate(self):
        return validate(self, TSG)
