from hades import db


class Access(db.Model):
    """
    Database model class
    """

    __tablename__ = "access"

    event = db.Column(
        db.String(50), db.ForeignKey("events.name"), nullable=False, primary_key=True
    )
    user = db.Column(
        db.String(20), db.ForeignKey("users.username"), nullable=False, primary_key=True
    )

    def __repr__(self):
        return "%r" % [self.event, self.user]
