from mongoengine import ValidationError, DynamicDocument, IntField, StringField

from hades import db

from requests import get

from hades.models.validate import ValidateMixin


class CodexApril2019(ValidateMixin, db.Model):
    """
    Database model class
    """

    __tablename__ = 'codex_april_2019'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(50), unique=True)
    phone = db.Column(db.String(21), unique=True)
    department = db.Column(db.String(50))

    def __repr__(self):
        return '%r' % [self.id, self.name, self.email, self.phone, self.department]


class RSC2019(ValidateMixin, db.Model):
    """
    Database model class
    """

    __tablename__ = 'rsc_2019'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(50), unique=True)
    phone = db.Column(db.String(21), unique=True)
    department = db.Column(db.String(50))
    year = db.Column(db.String(3))

    def __repr__(self):
        return '%r' % [
            self.id,
            self.name,
            self.email,
            self.phone,
            self.department,
            self.year,
        ]


class CodexDecember2019(ValidateMixin, db.Model):
    """
    Database model class
    """

    __tablename__ = 'codex_december_2019'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(62))
    email = db.Column(db.String(102), unique=True)
    phone = db.Column(db.String(21), unique=True)
    department = db.Column(db.String(20))
    year = db.Column(db.String(3))
    hackerrank_username = db.Column(db.String(50), unique=True)
    paid = db.Column(db.String(20))

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

    def validate(self):
        if (
            get(f'https://hackerrank.com/{self.hackerrank_username}')
            .content.decode()
            .count(self.hackerrank_username)
            < 3
        ):
            return f"Your hackerrank profile doesn't seem to exist!"

        if self.query.filter(
            CodexDecember2019.hackerrank_username == self.hackerrank_username
        ).first():
            return f"Someone has already registered with hackerrank username <code>{self.hackerrank_username}</code>.<br/>Kindly contact the team if that is your username and it wasn't your registration"
        return super().validate()


class BOV2020(DynamicDocument):
    """
    Database model class
    """

    @staticmethod
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

    id = IntField(primary_key=True)
    name = StringField()
    email = StringField(unique=True)
    phone = StringField()
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
