"""
General utility methods
"""

def beautifyOutputString(name):
    """
    Converts a string from the ontology into a more human-friendly string
    :param name: A formal resource name or URI
    :return: Beautified name
    """
    beauty = ''
    if name:
        from re import finditer
        beauty = name.replace('-', ' ')
        beauty = beauty.replace('_', ' ')
        matches = finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', beauty)  # find camelCase words
        groups = [m.group(0) for m in matches]
        beauty = ' '.join(groups)
    return beauty


def replaceLastCommaWithAnd(what):
    """
    Given a string containing a comma-separated list of elements, replace the last comma with 'and'
    :param what: string
    :return: string
    """
    processed = what
    if what:
        n = what.rfind(', ')
        if n > 0:
            processed = what[:n] + ' and ' + what[n+2:]
    return processed


def asWindows(unixpath):
    """
    Converts a Unix file path into its Windows equivalent
    :param unixpath: string
    :return: string; transformed input path
    """
    return unixpath.replace('/','\\')


def isNumber(n):
    """
    Checks whether the given string is a number
    :param n: The string to be checked
    :return boolean: True if the string can be converted to a float,
    False otherwise
    """
    try:
        float(n)
        return True
    except ValueError:
        return False
