from hades import db
from hades.models.validate import ValidateMixin


class Events(ValidateMixin, db.Model):
    """
    Database model class
    """

    __tablename__ = 'events'

    name = db.Column(db.String(50), primary_key=True)
    full_name = db.Column(db.String(60), unique=True)
