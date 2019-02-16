class Key(object):
    def __init__(self, text=''):
        """
        Learning Key constructor
        """
        self.text = text
        self.oe_id = None  # URI of a generic Ontology Element (string)
        self.instance_uris = []  # List of instance URIs of the same class (if relevant)
        self.triples = []  # Generic (s, p, value) triples used to id an specific Literal. Empty for non-Literals.

    def to_dict(self):
        """
        Converts this Key to an equivalent dictionary (of built-in types) representation
        :return: dict
        """
        d = {'text': self.text, 'oe_id': self.oe_id, 'triples': self.triples, 'instance_uris': self.instance_uris}
        return d

    def from_dict(self, d):
        """
        Populates this instances's attributes from the given dictionary
        :param d: dict
        :return: None; updates current instance
        """
        self.text = d.get('text', '')
        self.oe_id = d.get('oe_id')
        self.triples = [tuple(t) for t in d.get('triples', [])]
        self.instance_uris = d.get('instance_uris', [])

    def __eq__(self, other):
            if not isinstance(other, Key):
                return False
            elif self.text != other.text:
                return False
            elif self.oe_id != other.oe_id:
                return False
            elif self.triples != other.triples:
                return False
            elif self.instance_uris != other.instance_uris:
                return False
            else:
                return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        if self.triples:
            triple_str = r'"triples": ['
            first = True
            for triple in self.triples:
                if first:
                    first = False
                else:
                    triple_str += ", "
                triple_str += r'[' + ", ".join([r'"' + t + r'"' for t in triple]) + r']'
            triple_str += ']'
        else:
            triple_str = r'"triples": []'
        if self.instance_uris:
            inst_str = r'"instance_uris": ['
            first = True
            for uri in self.instance_uris:
                if first:
                    first = False
                else:
                    inst_str += ", "
                inst_str += r'"' + uri + r'"'
            inst_str += ']'
        else:
            inst_str = r'"instance_uris": []'
        if self.oe_id:
            oe_id_str = r'"oe_id": "' + self.oe_id + r'"'
        else:
            oe_id_str = r'"oe_id": null'
        return r'{"text": "' + self.text + r'", ' + oe_id_str + r', ' + triple_str + r', ' + inst_str + r'}'

    def __hash__(self):
        return hash(self.text) ^ hash(self.oe_id) ^ hash(tuple(self.triples)) ^ hash(tuple(self.instance_uris))
