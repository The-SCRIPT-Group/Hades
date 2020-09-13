from mongoengine import StringField, DynamicDocument

from hades.models.validate import EventMixin


class CSINovember2019(DynamicDocument, EventMixin):
    """
    Database model class
    """

    meta = {'collection': 'csi_november_2019'}
    department = StringField()
    year = StringField(max_length=3)
    csi_id = StringField(max_length=3, unique=True)

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


class CSINovemberNonMember2019(DynamicDocument, EventMixin):
    """
    Database model class
    """

    meta = {'collection': 'csi_november_non_member_2019'}

    department = StringField()
    year = StringField(max_length=3)
    prn = StringField(unique=True)
    paid = StringField()

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
