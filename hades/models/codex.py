from mongoengine import ValidationError, StringField, DynamicDocument
from requests import get

from hades.models.validate import EventMixin


class CodexApril2019(DynamicDocument, EventMixin):
    """
    Database model class
    """

    meta = {'collection': 'codex_april_2019'}

    department = StringField()

    def __repr__(self):
        return '%r' % [self.id, self.name, self.email, self.phone, self.department]


class RSC2019(DynamicDocument, EventMixin):
    """
    Database model class
    """

    meta = {'collection': 'rsc_2019'}

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


class CodexDecember2019(DynamicDocument, EventMixin):
    """
    Database model class
    """

    def __validate_hackerrank_username__(username):
        """
        Validate if hackerrank username exists
        :param username: hackerrank username to test
        :return: None, raise error if username doesn't exist
        """
        if (
            get(f'https://hackerrank.com/{username}').content.decode().count(username)
            < 3
        ):
            raise ValidationError("Your hackerrank profile doesn't seem to exist!")

    meta = {'collection': 'codex_december_2019'}

    department = StringField()
    year = StringField(max_length=3)
    hackerrank_username = StringField(
        unique=True, validation=__validate_hackerrank_username__
    )
    paid = StringField()

    def __repr__(self):
        return '%r' % [
            self.id,
            self.name,
            self.email,
            self.phone,
            self.department,
            self.year,
            self.hackerrank_username,
            self.paid,
        ]


class BOV2020(DynamicDocument, EventMixin):
    """
    Database model class
    """

    def __validate_hackerrank_username__(username):
        """
        Validate if hackerrank username exists
        :param username: hackerrank username to test
        :return: None, raise error if username doesn't exist
        """
        if (
            get(f'https://hackerrank.com/{username}').content.decode().count(username)
            < 3
        ):
            raise ValidationError("Your hackerrank profile doesn't seem to exist!")

    meta = {'collection': 'bov_2020'}

    hackerrank_username = StringField(
        unique=True, validation=__validate_hackerrank_username__
    )
    country = StringField()

    def __repr__(self):
        return '%r' % [
            self.id,
            self.name,
            self.email,
            self.phone,
            self.hackerrank_username,
            self.country,
        ]
