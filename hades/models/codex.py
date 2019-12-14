from hades import db
from hades.utils import validate


class CodexApril2019(db.Model):
    """
    Database model class
    """

    __tablename__ = "codex_april_2019"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(50), unique=True)
    phone = db.Column(db.String(21), unique=True)
    department = db.Column(db.String(50))

    def __repr__(self):
        return "%r" % [self.id, self.name, self.email, self.phone, self.department]

    def validate(self):
        return validate(self, CodexApril2019)


class RSC2019(db.Model):
    """
    Database model class
    """

    __tablename__ = "rsc_2019"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(50), unique=True)
    phone = db.Column(db.String(21), unique=True)
    department = db.Column(db.String(50))
    year = db.Column(db.String(3))

    def __repr__(self):
        return "%r" % [
            self.id,
            self.name,
            self.email,
            self.phone,
            self.department,
            self.year,
        ]

    def validate(self):
        return validate(self, RSC2019)


class CodexDecember2019(db.Model):
    """
    Database model class
    """

    __tablename__ = "codex_december_2019"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(62))
    email = db.Column(db.String(102), unique=True)
    phone = db.Column(db.String(21), unique=True)
    department = db.Column(db.String(50))
    department_2 = db.Column(db.String(50))
    year = db.Column(db.String(3))
    hackerrank_username = db.Column(db.String(50), unique=True)
    noqr_paid = db.Column(db.String(20))

    def __repr__(self):
        return "%r" % [
            self.id,
            self.name,
            self.email,
            self.phone,
            self.department,
            self.department_2,
            self.year,
            self.hackerrank_username,
            self.noqr_paid,
        ]

    def validate(self):
        for user in db.session.query(CodexDecember2019).all():
            if self.hackerrank_username == user.hackerrank_username:
                return f"Someone has already registered with hackerrank username <code>{self.hackerrank_username}</code>.<br/>Kindly contact the team if that is your username and it wasn't your registration"
        return validate(self, CodexDecember2019)
