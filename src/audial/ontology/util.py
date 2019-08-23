"""
Ontology utility methods
"""


def stringToID(what, thing_type='entity'):
    """
    Converts a free-formed string to the format of ontology elements
    :param what: input string
    :param thing_type: the type of element to consider: entity, property, instance
    :return: string
    """
    norm_string = ''
    if what:
        import re
        norm_string = re.sub(r"\s+", '_', what)
        if 'Property' not in thing_type and 'property' not in thing_type:
            # Words may start with uppercase
            words = norm_string.split("_")
            norm_string = '_'.join([w.title() for w in words])
    return norm_string


def getNamespace(uri):
    """
    Returns the namespace of the given URI
    :param item: an element's URI
    :return: The namespace part of the URI
    """
    ns = ''
    if uri and '#' in uri:
        return uri.split('#')[0]
    return ns


def stripNamespace(uri):
    """
    Returns the name of the given item without the namespace prefix
    :param uri: an instance's URI
    :return string: resource name without NS prefix
    """
    if uri:
        if '#' in uri:
            return uri.split('#')[1]
        else:
            return str(uri)
    return uri
