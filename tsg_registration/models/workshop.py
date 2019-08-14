from tsg_registration import db


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


class CCPPWSMay2019(db.Model):
    """
    Database model class
    """

    __tablename__ = "c_cpp_workshop_september_2019"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(50), unique=True)
    phone = db.Column(db.String(21), unique=True)

    def __repr__(self):
        return "%r" % [self.id, self.name, self.email, self.phone]
