from hades import db


class TestTable(db.Model):
    """
    Database model class
    """

    __tablename__ = "test_users"
    name = db.Column(db.String())
    email = db.Column(db.String(), primary_key=True)
