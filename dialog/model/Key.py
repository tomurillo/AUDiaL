class Key(object):
    def __init__(self, text=''):
        """
        Learning Key constructor
        """
        self.text = text
        self.oe = None  # Ontology Element

    def __eq__(self, other):
            if type(other) is not Key:
                return False
            elif self.text != other.text:
                return False
            elif self.oe != other.oe:
                return False
            else:
                return True

    def __ne__(self, other):
        return not self.__eq__(other)
