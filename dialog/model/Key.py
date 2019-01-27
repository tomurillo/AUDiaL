class Key(object):
    def __init__(self, text=''):
        """
        Learning Key constructor
        """
        self.text = text
        self.oe_id = None  # URI of a generic Ontology Element (string)
        self.triples = []  # Generic (s, p, value) triples used to id an specific Literal. Empty for non-Literals.

    def __eq__(self, other):
            if not isinstance(other, Key):
                return False
            elif self.text != other.text:
                return False
            elif self.oe_id != other.oe_id:
                return False
            elif self.triples != other.triples:
                return False
            else:
                return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        if self.triples:
            id_str = str(self.triples)
        else:
            id_str = self.oe_id
        return 'Key: ' + self.text + id_str

    def __hash__(self):
        return hash(self.text) ^ hash(self.oe_id) ^ hash(tuple(self.triples))
