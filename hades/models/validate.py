from typing import Union

from hades import db


class ValidateMixin(object):
    def validate(self) -> Union[str, bool]:
        table = self.__class__
        # Ensure nobody else in the table has the same email address
        if db.session.query(table).filter(table.email == self.email).first():
            return f'Email address {self.email} already found in database! Please re-enter the form correctly!'

        # Ensure nobody else in the table has the same phone number
        for num in self.phone.split('|'):
            if db.session.query(table).filter(table.phone.like(f'%{num}%')).first():
                return f'Phone number {num} already found in database! Please re-enter the form correctly!'

        return True
