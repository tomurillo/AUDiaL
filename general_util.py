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


def truncateString(what, length=80, dots='...'):
    """
    Truncates a string to the given length
    :param what: string; string to truncate
    :param length: int; position from which the string gets truncated
    :param dots: string; something to append at the end of the truncated string
    :return: string; truncated string
    """
    if len(what) > length:
        return what[: length] + dots
    else:
        return what


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


def stringOpToPython(string_op, negate=False):
    """
    Converts a string representation of an operator to its Python equivalent
    :param string_op: an operator e.g. '>', '<', '=', '>=', '<='
    :return: an equivalent operator function
    """
    import operator
    op = None
    ops = {'>': operator.gt, '<': operator.lt, '=': operator.eq
        , '<=': operator.le, '>=': operator.ge, '!=': operator.ne}
    negops = {'<=': operator.gt, '>=': operator.lt, '!=': operator.eq
        , '>': operator.le, '<': operator.ge, '=': operator.ne}
    if string_op in ops:
        if negate:
            op = negops[string_op]
        else:
            op = ops[string_op]
    return op


def numberToOrdinal(n):
    """
    Return the ordinal equivalent of the given number
    :param n: int; a number
    :return: string; ordinal representation of n e.g. "1st", "2nd", etc.
    """
    return "%d%s" % (n, "tsnrhtdd"[(n / 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])


def isNumber(n):
    """
    Checks whether the given string is a number
    :param n: The string to be checked
    :return boolean: True if the string can be converted to a float, False otherwise
    """
    try:
        float(n)
        return True
    except ValueError:
        return False


def deleteDirContents(path, ignore=None):
    """
    Delete all contents of the given directory
    :param path: string; absolute path to a directory
    :param ignore: list<string>; files to spare from being deleted
    :return: None
    """
    import os, shutil
    if os.path.isdir(path):
        if ignore is None:
            ignore = []
        for root, dirs, files in os.walk(path):
            for f in files:
                if f not in ignore:
                    os.unlink(os.path.join(root, f))
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))
