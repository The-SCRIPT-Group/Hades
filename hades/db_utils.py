from typing import Union, List

from mongoengine import Document, errors

from hades.models.user import TSG


def insert(objects: List[Document]) -> (bool, str):
    """
    Function to insert the given objects into the database
    :param objects: List of objects to be added to the database
    :return: success, and reason if failure (empty on success)
    """
    try:
        for doc in objects:
            doc.save()
    except Exception as e:
        if e.__class__ == errors.NotUniqueError:
            return False, 'not_unique'
        return False, f'{e.__class__} occurred - {e}'
    return True, ''


def get_user(table: Document, id_: str) -> Union[Document, None]:
    """
    Function to check whether a given id exists in a collection or not
    :param table: The table object
    :param id_: The value of the ID
    :return: User object if it exists, else None
    """
    return table.objects(pk=id_).first()


def get_data_from_table(table: Document) -> Union[list, None]:
    """
    Function to get all docs from the specified table
    :param table: The collection whose docs are to be retrieved
    :return: List of all docs
    """
    return table.objects


def update_doc(user: Document, column: str, value) -> (bool, str):
    """
    Function to update a single value in the given doc
    :param user: The object of that user
    :param column: The name of the field
    :param value: The updated value
    :return: success, and reason if failure (empty on success)
    """
    temp = getattr(user, column)
    if temp == value:
        return True, ''
    setattr(user, column, value)
    try:
        user.save()
    except Exception as e:
        return False, f'{e.__class__} occurred - {e}'
    return True, ''


def delete_row_from_table(user: Document) -> (bool, str):
    """
    Function to delete a user (i.e. a single document)
    :param user: The object of that user
    :return: success, and reason if failure (empty on success)
    """
    try:
        user.delete()
    except Exception as e:
        return False, f'{e.__class__} occurred - {e}'
    return True, ''


def save_user(user: Document) -> (bool, str):
    """
    Function to save the changes in given user object in the database
    :param user: The user whose object is to be saved
    :return: success, and reason if failure (empty on success)
    """
    try:
        user.save()
    except Exception as e:
        return False, f'{e.__class__} occurred - {e}'
    return True, ''


def is_user_tsg(email: str) -> bool:
    """
    Function to check if the email address used belongs to a TSG member
    :param email: Email address
    :return: True if a member, False if not
    """
    return TSG.objects(email=email).first() is not None
