from NLP.model.SemanticConcept import *


class SuggestionKey(object):
    def __init__(self, text=''):
        """
        Dialog Suggestion Key constructor
        """
        self.text = text  # Text that needs clarification
        self.nearest_neighbors = []  # List of SemanticConcept nearest neighbors (context of self.text)

    def to_dict(self):
        """
        Converts this SuggestionKey to an equivalent dictionary (of built-in types) representation
        :return: dict
        """
        d = {'text': self.text, 'nearest_neighbors': [nn.to_dict() for nn in self.nearest_neighbors]}
        return d

    def from_dict(self, d):
        """
        Populates this instances's attributes from the given dictionary
        :param d: dict
        :return: None; updates current instance
        """
        self.text = d.get('text', '')
        nn_list = d.get('nearest_neighbors', [])
        nn_sc_list = []
        for nn in nn_list:
            nn_sc = SemanticConcept()
            nn_sc.from_dict(nn)
            nn_sc_list.append(nn_sc)
        self.nearest_neighbors = nn_sc_list

    def __eq__(self, other):
            if type(other) is not SuggestionKey:
                return False
            elif self.text != other.text:
                return False
            elif self.nearest_neighbors != other.nearest_neighbors:
                return False
            else:
                return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.text) ^ hash(tuple(self.nearest_neighbors))
