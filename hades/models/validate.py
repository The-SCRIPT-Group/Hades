from mongoengine import DynamicDocument, ValidationError, StringField, IntField


class EventMixin(DynamicDocument):
    """
    Class with common fields and validation
    """

    meta = {'allow_inheritance': True}

    @staticmethod
    def __validate_phone__(phone):
        """
        Ensure nobody else in the table has the same phone number
        :param phone: phone number to be checked
        """
        for num in phone.split('|'):
            if len(str(num)) < 10:
                raise ValidationError(
                    f'Phone number {num} is too short! Please re-enter the form correctly!'
                )

    id = IntField(primary_key=True)
    name = StringField()
    phone = StringField(validation=__validate_phone__, required=True)
    email = StringField(
        unique=True,
        regex=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$",
        required=True,
    )
