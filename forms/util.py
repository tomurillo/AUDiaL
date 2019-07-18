import os
import errno
import json


def getStoragePath(filename, username):
    """
    Returns the platform-specific path to a form data storage file
    :param filename: string; name of the file where to serialize the data
    :param username: string; current user name; will be used as directory name for the user's data
    :return: string; absolute path to the storage file
    """
    path = ''
    dir_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "storage", username))
    try:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        path = os.path.normpath(os.path.join(dir_path, filename))
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    return path


def loadSerializedForm(filename_base, username):
    """
    Retrieve the values from a serialized form on disk
    :param filename_base: string; unique string which the final filename is based on
    :param username: string; current user name
    :return: dict; form values keyed by element name
    """
    store_path = getStoragePath("%s-raw.json" % filename_base, username)
    form_values = {}
    if os.path.isfile(store_path):
        with open(store_path, 'r') as f:
            form_values = json.load(f)
    return form_values


def serializeForm(form, filename_base, username):
    """
    Serialize and store form data for later retrieval.
    :param form: dict with form values
    :param filename_base: string; unique string on which to base the final filename
    :param username: string; current user name; used as directory name for the user's data
    :return: None, form is serialized to disk
    """
    if form:
        store_path = getStoragePath("%s-raw.json" % filename_base, username)
        with open(store_path, 'w') as f:
            f.write(json.dumps(form))
