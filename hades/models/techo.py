from hades import db
from hades.models.validate import ValidateMixin


class EHJuly2019(ValidateMixin, db.Model):
    """
    Database model class
    """

    __tablename__ = 'eh_july_2019'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(50), unique=True)
    phone = db.Column(db.String(21), unique=True)
    department = db.Column(db.String(50))

    def __repr__(self):
        return '%r' % [self.id, self.name, self.email, self.phone, self.department]

    def validate(self):
        return super().validate()


class P5November2019(ValidateMixin, db.Model):
    """
    Database model class
    """

    __tablename__ = 'p5_november_2019'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(50), unique=True)
    phone = db.Column(db.String(21), unique=True)
    department = db.Column(db.String(50))
    year = db.Column(db.String(3))
    level = db.Column(db.String(12))

    def __repr__(self):
        return '%r' % [
            self.id,
            self.name,
            self.email,
            self.phone,
            self.department,
            self.year,
            self.level,
        ]

    def validate(self):
        return super().validate()
