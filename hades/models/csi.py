from hades import db
from hades.models.validate import ValidateMixin


class CSINovember2019(ValidateMixin, db.Model):
    """
    Database model class
    """

    __tablename__ = 'csi_november_2019'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(50), unique=True)
    phone = db.Column(db.String(21), unique=True)
    department = db.Column(db.String(50))
    year = db.Column(db.String(3))
    csi_id = db.Column(db.String(3), unique=True)

    def __repr__(self):
        return '%r' % [
            self.id,
            self.name,
            self.email,
            self.phone,
            self.department,
            self.year,
            self.csi_id,
        ]

    def validate(self):
        if self.query.filter(CSINovember2019.csi_id == self.csi_id).first():
            return f'CSI ID {self.csi_id} is already registered in the database'
        return super().validate()


class CSINovemberNonMember2019(ValidateMixin, db.Model):
    """
    Database model class
    """

    __tablename__ = 'csi_november_non_member_2019'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(50), unique=True)
    phone = db.Column(db.String(21), unique=True)
    department = db.Column(db.String(50))
    year = db.Column(db.String(3))
    prn = db.Column(db.String(10), unique=True)
    paid = db.Column(db.String(20))

    def __repr__(self):
        return '%r' % [
            self.id,
            self.name,
            self.email,
            self.phone,
            self.department,
            self.year,
            self.prn,
        ]

    def validate(self):
        if self.query.filter(CSINovemberNonMember2019.prn == self.prn).first():
            return f'PRN {self.prn} is already registered in the database'
        return super().validate()
