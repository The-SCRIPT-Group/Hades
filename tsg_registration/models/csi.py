from tsg_registration import db
from tsg_registration.utils import validate


class CSINovember2019(db.Model):
    """
    Database model class
    """

    __tablename__ = "csi_november_2019"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(50), unique=True)
    phone = db.Column(db.String(21), unique=True)
    department = db.Column(db.String(50))
    year = db.Column(db.String)

    prn = db.Column(db.Integer, unique=True)
    csi_id = db.Column(db.String(3), unique=True)

    def __repr__(self):
        return "%r" % [
            self.id,
            self.name,
            self.email,
            self.phone,
            self.department,
            self.year,
            self.prn,
            self.csi_id,
        ]

    def validate(self):
        return validate(self, CSINovember2019)
