from tsg_registration import db


class Access(db.Model):
    """
    Database model class
    """

    __tablename__ = "access"

    event = db.Column(
        db.String(), db.ForeignKey("events.name"), nullable=False, primary_key=True
    )
    user = db.Column(
        db.String(), db.ForeignKey("users.username"), nullable=False, primary_key=True
    )
