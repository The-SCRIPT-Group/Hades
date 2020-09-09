from mongoengine import StringField, DynamicDocument


class Events(DynamicDocument):
    """
    Database model class
    """

    meta = {'collection': 'events'}

    name = StringField(primary_key=True)
    full_name = StringField(unique=True)
