from mongoengine import DynamicDocument, IntField, StringField


class TestTable(DynamicDocument):
    """
    Database model class
    """

    meta = {'collection': 'test_users'}

    id = IntField(primary_key=True)
    name = StringField()
    email = StringField(unique=True)
    phone = StringField(unique=True)

    def __repr__(self):
        return '%r' % [self.id, self.name, self.email, self.phone]


class NewEvent(DynamicDocument):
    """
    Database model class
    """

    meta = {'collection': 'new_event'}

    id = IntField(primary_key=True)
    name = StringField()
    email = StringField(unique=True)
    phone = StringField(unique=True)

    def __repr__(self):
        return '%r' % [self.id, self.name, self.email, self.phone]
