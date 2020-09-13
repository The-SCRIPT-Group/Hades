from flask_bcrypt import Bcrypt
from flask_login import UserMixin
from mongoengine import (
    DynamicDocument,
    IntField,
    StringField,
    ListField,
    ReferenceField,
    CASCADE,
)

from hades import app
from hades.models.event import Events

bcrypt = Bcrypt(app)


class Users(DynamicDocument, UserMixin):
    """
    Database model class
    """

    meta = {'collection': 'users'}

    name = StringField()
    username = StringField(primary_key=True)
    password = StringField()
    email = StringField(unique=True)
    access = ListField(ReferenceField(Events, reverse_delete_rule=CASCADE))

    def get_id(self):
        return self.username if self is not None else None

    def check_password_hash(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password, password)

    def generate_password_hash(self, password: str):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def __repr__(self):
        return '%r' % [self.username, self.name, self.email]


class TSG(DynamicDocument):
    """
    Database model class
    """

    meta = {'collection': 'tsg'}

    id = IntField(primary_key=True)
    name = StringField()
    email = StringField(unique=True)
    phone = StringField(unique=True)

    def __repr__(self):
        return '%r' % [self.id, self.name, self.email, self.phone]
