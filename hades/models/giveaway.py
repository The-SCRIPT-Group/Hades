from hades import db
from hades.models.validate import ValidateMixin


class Coursera2020(ValidateMixin, db.Model):
    """
    Database model class
    """

    __tablename__ = 'coursera_2020'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(50), unique=True)
    phone = db.Column(db.String(10), unique=True)
    prn = db.Column(db.String(10), unique=True)
    faculty = db.Column(db.String(30))
    school = db.Column(db.String(25))
    program = db.Column(db.String(35))
    year = db.Column(db.Integer())

    def __repr__(self):
        return '%r' % [
            self.id,
            self.name,
            self.email,
            self.phone,
            self.prn,
            self.faculty,
            self.school,
            self.program,
            self.year,
        ]

    def validate(self):
        if db.session.query(Coursera2020).filter(Coursera2020.prn == self.prn).first():
            return f'PRN {self.prn} is already registered in the database'
        return super().validate()
