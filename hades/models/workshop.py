from hades import db
from hades.models.validate import ValidateMixin


class CPPWSMay2019(ValidateMixin, db.Model):
    """
    Database model class
    """

    __tablename__ = 'cpp_workshop_may_2019'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(50), unique=True)
    phone = db.Column(db.String(21), unique=True)

    def __repr__(self):
        return '%r' % [self.id, self.name, self.email, self.phone]


class CCPPWSAugust2019(ValidateMixin, db.Model):
    """
    Database model class
    """

    __tablename__ = 'c_cpp_workshop_august_2019'
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

    def validate(self):
        if self.year == '1st':
            return super().validate()
        return 'This workshop is <b>only</b> for FY students'


class Hacktoberfest2019(ValidateMixin, db.Model):
    """
    Database model class
    """

    __tablename__ = 'do_hacktoberfest_2019'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(50), unique=True)
    phone = db.Column(db.String(21), unique=True)
    department = db.Column(db.String(50))
    year = db.Column(db.String(3))
    date = db.Column(db.String(2))

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


class CNovember2019(ValidateMixin, db.Model):
    """
    Database model class
    """

    __tablename__ = 'c_november_2019'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(50), unique=True)
    phone = db.Column(db.String(21), unique=True)
    year = db.Column(db.String(3))
    prn = db.Column(db.Integer, unique=True)
    roll = db.Column(db.String(4), unique=True)

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

    def validate(self):
        if self.year == '2nd':
            return super().validate()
        if (
            db.session.query(CNovember2019)
            .filter(CNovember2019.prn == self.prn)
            .first()
        ):
            return f'PRN {self.prn} has already been registered!'
        if (
            db.session.query(CNovember2019)
            .filter(CNovember2019.roll == self.roll)
            .first()
        ):
            return f'Roll number {self.roll} has already been registered!'
        return 'This workshop is <b>only</b> for SY students'


class BitgritDecember2019(ValidateMixin, db.Model):
    """
    Database model class
    """

    __tablename__ = 'bitgrit_december_2019'
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
