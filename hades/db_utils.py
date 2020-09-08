from typing import Union, List

from flask_sqlalchemy import Model
from sqlalchemy.exc import DataError, IntegrityError

from hades import db
from hades.models.user import TSG


def insert(objects: List[Model]) -> (bool, str):
    """
    Function to insert the given objects into the database
    :param objects: List of objects to be added to the database
    :return: success, and reason if failure (empty on success)
    """
    try:
        for user in objects:
            db.session.add(user)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return False, f'IntegrityError occurred - {e}'
    except DataError as e:
        db.session.rollback()
        return False, f'DataError occurred - {e}'
    return True, ''


def get_user(table: Model, id_: str) -> Union[Model, None]:
    """
    Function to check whether a given id exists in a table or not
    :param table: The table object
    :param id_: The value of the ID
    :return: User object if it exists, else None
    """
    return table.query.get(id_)


def get_data_from_table(table: Model) -> Union[list, None]:
    """
    Function to get all rows from the specified table
    :param table: The table whose rows are to be retrieved
    :return: List of all rows
    """
    return table.query.all()


def update_row_in_table(user: Model, column: str, value) -> (bool, str):
    """
    Function to update a single value in a single row in the given table
    :param user: The object of that user
    :param column: The name of the field
    :param value: The updated value
    :return: success, and reason if failure (empty on success)
    """
    temp = getattr(user, column)
    setattr(user, column, value)
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        setattr(user, column, temp)
        return False, f'IntegrityError occurred - {e}'
    except DataError as e:
        db.session.rollback()
        setattr(user, column, temp)
        return False, f'DataError occurred - {e}'
    return True, ''


def commit_transaction() -> (bool, str):
    """
    Function to commit the current changes in the database
    :return: success, and reason if failure (empty on success)
    """
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return False, f'IntegrityError occurred - {e}'
    except DataError as e:
        db.session.rollback()
        return False, f'DataError occurred - {e}'
    return True, ''


def is_user_tsg(email: str) -> bool:
    """
    Function to check if the email address used belongs to a TSG member
    :param email: Email address
    :return: True if a member, False if not
    """
    return TSG.query.filter(TSG.email == email).first() is not None
