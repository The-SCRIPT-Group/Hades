from hades import db


class TestTable(db.Model):
    """
    Database model class
    """

    __tablename__ = "test_users"
    name = db.Column(db.String(30))
    email = db.Column(db.String(50), primary_key=True)
