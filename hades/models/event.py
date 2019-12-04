from hades import db


class Events(db.Model):
    """
    Database model class
    """

    __tablename__ = "events"

    name = db.Column(db.String(), primary_key=True)
    full_name = db.Column(db.String(), unique=True)
