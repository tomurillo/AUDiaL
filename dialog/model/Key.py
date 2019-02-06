class Key(object):
    def __init__(self, text=''):
        """
        Learning Key constructor
        """
        self.text = text
        self.oe_id = None  # URI of a generic Ontology Element (string)
        self.triples = []  # Generic (s, p, value) triples used to id an specific Literal. Empty for non-Literals.

    def to_dict(self):
        """
        Converts this Key to an equivalent dictionary (of built-in types) representation
        :return: dict
        """
        d = {'text': self.text, 'oe_id': self.oe_id, 'triples': self.triples}
        return d

    def from_dict(self, d):
        """
        Populates this instances's attributes from the given dictionary
        :param d: dict
        :return: None; updates current instance
        """
        self.text = d.get('text', '')
        self.oe_id = d.get('oe_id')
        self.triples = d.get('triples', [])

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
            triple_str = '\'triples\': ['
            for uri in self.triples:
                triple_str += '\'' + uri + '\''
            triple_str = ']'
        else:
            triple_str = '\'triples\': []'
        if self.oe_id:
            oe_id_str = '\'oe_id\': \'' + self.oe_id + '\''
        else:
            oe_id_str = '\'oe_id\': None'
        return '{\'text\': \'' + self.text + '\', ' + oe_id_str + ', ' + triple_str + '}'

    def __hash__(self):
        return hash(self.text) ^ hash(self.oe_id) ^ hash(tuple(self.triples))
