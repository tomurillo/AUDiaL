import os
import errno


def getStoragePath(filename, username):
    """
    Returns the platform-specific path to a form data storage file
    :param username: string; name of the file where to serialze the data
    :param username: string; current user name; will be used as directory name for the user's data
    :return: string; absolute path to the json file with the serialized learning model
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
