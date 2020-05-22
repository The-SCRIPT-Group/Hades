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

        if (
            db.session.query(CodexDecember2019)
            .filter(CodexDecember2019.hackerrank_username == self.hackerrank_username)
            .first()
        ):
            return f"Someone has already registered with hackerrank username <code>{self.hackerrank_username}</code>.<br/>Kindly contact the team if that is your username and it wasn't your registration"
        return super().validate()


class BOV2020(ValidateMixin, db.Model):
    """
    Database model class
    """

    __tablename__ = 'bov_2020'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(31))
    email = db.Column(db.String(51), unique=True)
    phone = db.Column(db.String(19))
    hackerrank_username = db.Column(db.String(50), unique=True)
    country = db.Column(db.String(24))

    def __repr__(self):
        return '%r' % [
            self.id,
            self.name,
            self.email,
            self.phone,
            self.hackerrank_username,
            self.country,
        ]

    def validate(self):
        if (
            get(f'https://hackerrank.com/{self.hackerrank_username}')
            .content.decode()
            .count(self.hackerrank_username)
            < 3
        ):
            return f"Your hackerrank profile doesn't seem to exist!"

        if (
            db.session.query(BOV2020)
            .filter(BOV2020.hackerrank_username == self.hackerrank_username)
            .first()
        ):
            return f"Someone has already registered with hackerrank username <code>{self.hackerrank_username}</code>.<br/>Kindly contact the team if that is your username and it wasn't your registration"
        return super().validate()
