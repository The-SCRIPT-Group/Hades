from hades import db

from flask_login import UserMixin


class Users(db.Model, UserMixin):
    """
    Database model class
    """

    __tablename__ = "users"
    name = db.Column(db.String(30))
    username = db.Column(db.String(20), primary_key=True)
    password = db.Column(db.String(100))
    api_key = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(50), unique=True)

    def get_id(self):
        return self.username if self is not None else None