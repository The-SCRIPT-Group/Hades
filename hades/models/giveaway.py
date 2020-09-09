from mongoengine import IntField, StringField

from hades import db
from hades.models.validate import ValidateMixin


class Coursera2020(ValidateMixin):
    """
    Database model class
    """

    meta = {'collection': 'coursera_2020'}

    prn = StringField(unique=True)
    faculty = StringField()
    school = StringField()
    program = StringField()
    year = IntField()

    def __repr__(self):
        return '%r' % [
            self.id,
            self.name,
            self.email,
            self.phone,
            self.prn,
            self.faculty,
            self.school,
            self.program,
            self.year,
        ]
