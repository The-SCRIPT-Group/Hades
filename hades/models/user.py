from random import choice
from string import ascii_letters, digits, punctuation

from flask_bcrypt import Bcrypt
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


class Users(DynamicDocument):
    """
    Database model class
    """

    meta = {'collection': 'users'}

    name = StringField()
    username = StringField(primary_key=True)
    password = StringField()
    api_key = StringField(unique=True)
    email = StringField(unique=True)
    access = ListField(ReferenceField(Events, reverse_delete_rule=CASCADE))

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
