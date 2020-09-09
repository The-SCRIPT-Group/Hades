from mongoengine import StringField, IntField

from hades.models.validate import ValidateMixin


class CPPWSMay2019(ValidateMixin):
    """
    Database model class
    """

    meta = {'collection': 'cpp_workshop_may_2019'}

    def __repr__(self):
        return '%r' % [self.id, self.name, self.email, self.phone]


class CCPPWSAugust2019(ValidateMixin):
    """
    Database model class
    """

    meta = {'collection': 'c_cpp_workshop_august_2019'}

    department = StringField()
    year = StringField(choices=['1st'])

    def __repr__(self):
        return '%r' % [
            self.id,
            self.name,
            self.email,
            self.phone,
            self.department,
            self.year,
        ]


class Hacktoberfest2019(ValidateMixin):
    """
    Database model class
    """

    meta = {'collection': 'do_hacktoberfest_2019'}

    department = StringField()
    year = StringField(max_length=3)
    date = StringField(max_length=2)

    def __repr__(self):
        return '%r' % [
            self.id,
            self.name,
            self.email,
            self.phone,
            self.department,
            self.year,
            self.date,
        ]


class CNovember2019(ValidateMixin):
    """
    Database model class
    """

    __tablename__ = 'c_november_2019'

    year = StringField(choices=['2nd'])
    prn = IntField(unique=True)
    roll = StringField(max_length=4, unique=True)

    def __repr__(self):
        return '%r' % [
            self.id,
            self.name,
            self.email,
            self.phone,
            self.year,
            self.prn,
            self.roll,
        ]


class BitgritDecember2019(ValidateMixin):
    """
    Database model class
    """

    meta = {'collection': 'bitgrit_december_2019'}

    department = StringField()
    year = StringField(max_length=3)

    def __repr__(self):
        return '%r' % [
            self.id,
            self.name,
            self.email,
            self.phone,
            self.department,
            self.year,
        ]
