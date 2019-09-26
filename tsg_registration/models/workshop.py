from tsg_registration import db
from tsg_registration.utils import validate


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
    year = db.Column(db.String)

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
    year = db.Column(db.String)
    miscellaneous = db.Column(db.String)

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
        return validate(self, CPPWSMay2019)
