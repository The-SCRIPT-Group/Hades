from hades import db


class Coursera2020(db.Model):
    """
    Database model class
    """

    __tablename__ = 'coursera_2020'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(50), unique=True)
    phone = db.Column(db.String(10), unique=True)
    prn = db.Column(db.Integer(10), unique=True)
    faculty = db.Column(db.String(30))
    school = db.Column(db.String(25))
    program = db.Column(db.String(35))
    year = db.Column(db.Integer(1))

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
