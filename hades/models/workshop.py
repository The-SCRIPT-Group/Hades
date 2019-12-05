from hades import db
from hades.utils import validate


class CPPWSMay2019(db.Model):
    """
    Database model class
    """

    __tablename__ = "cpp_workshop_may_2019"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(50), unique=True)
    phone = db.Column(db.String(21), unique=True)

    def __repr__(self):
        return "%r" % [self.id, self.name, self.email, self.phone]

    def validate(self):
        return validate(self, CPPWSMay2019)


class CCPPWSAugust2019(db.Model):
    """
    Database model class
    """

    __tablename__ = "c_cpp_workshop_august_2019"
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
        if self.year == "1st":
            return validate(self, CCPPWSAugust2019)
        return "This workshop is <b>only</b> for FY students"


class Hacktoberfest2019(db.Model):
    """
    Database model class
    """

    __tablename__ = "do_hacktoberfest_2019"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(50), unique=True)
    phone = db.Column(db.String(21), unique=True)
    department = db.Column(db.String(50))
    year = db.Column(db.String(3))
    miscellaneous = db.Column(db.String(2))

    def __repr__(self):
        return "%r" % [
            self.id,
            self.name,
            self.email,
            self.phone,
            self.department,
            self.year,
            self.miscellaneous,
        ]

    def validate(self):
        return validate(self, Hacktoberfest2019)


class CNovember2019(db.Model):
    """
    Database model class
    """

    __tablename__ = "c_november_2019"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(50), unique=True)
    phone = db.Column(db.String(21), unique=True)
    year = db.Column(db.String(3))
    prn = db.Column(db.Integer, unique=True)
    roll = db.Column(db.String(4), unique=True)

    def __repr__(self):
        return "%r" % [
            self.id,
            self.name,
            self.email,
            self.phone,
            self.year,
            self.prn,
            self.roll,
        ]

    def validate(self):
        if self.year == "2nd":
            return validate(self, CNovember2019)
        for user in db.session.query(CNovember2019).all():
            if user.prn == self.prn:
                return f"PRN {self.prn} has already been registered!"
            if user.roll == self.roll:
                return f"Roll number {self.roll} has already been registered!"
        return "This workshop is <b>only</b> for SY students"
        4


class BitgritDecember2019(db.Model):
    """
    Database model class
    """

    __tablename__ = "bitgrit_december_2019"
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
        return validate(self, BitgritDecember2019)
