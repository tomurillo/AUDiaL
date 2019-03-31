from NLP.model.SemanticConcept import *
from NLP.model.POC import *
import uuid


class Vote(object):
    def __init__(self):
        """
        Vote constructor
        """
        self.id = str(uuid.uuid4())
        self.vote = -1.0
        self.candidate = None  # Candidate SemanticConcept or POC instance

    def to_dict(self):
        """
        Converts this Vote to an equivalent dictionary (of built-in types) representation
        :return: dict
        """
        d = {'id': self.id, 'vote': self.vote}
        if self.candidate:
            d['candidate'] = self.candidate.to_dict()
        else:
            d['candidate'] = None
        return d

    def from_dict(self, d):
        """
        Populates this instances's attributes from the given dictionary
        :param d: dict
        :return: None; updates current instance
        """
        self.id = d.get('id', '')
        self.vote = d.get('vote', -1.0)
        self.candidate = None
        candidate_dict = d.get('candidate')
        if candidate_dict:
            candidate_type = candidate_dict.get('type')
            if candidate_type == 'POC':
                candidate = POC()
            else:
                candidate = SemanticConcept()
            candidate.from_dict(candidate_dict)
            self.candidate = candidate

    def __eq__(self, other):
        if not isinstance(other, Vote):
            return False
        elif self.id != other.id:
            return False
        elif self.vote != other.vote:
            return False
        elif self.candidate != other.candidate:
            return False
        else:
            return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.id) ^ hash(self.vote) ^ hash(self.candidate)
