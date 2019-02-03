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


def asWindows(unixpath):
    """
    Converts a Unix file path into its Windows equivalent
    :param unixpath: string
    :return: string; transformed input path
    """
    return unixpath.replace('/','\\')
