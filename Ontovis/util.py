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
