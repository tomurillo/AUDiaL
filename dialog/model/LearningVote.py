from NLP.model.SemanticConcept import *
import uuid


class LearningVote(object):
    def __init__(self):
        """
        LearningVote constructor
        """
        self.id = str(uuid.uuid4())
        self.identifier = None  # OntologyElement instance candidate
        self.score = -1.0
        self.task = None

    def to_dict(self):
        """
        Converts this LearningVote to an equivalent dictionary (of built-in types) representation
        :return: dict
        """
        d = {'id': self.id, 'score': self.score, 'task': self.task}
        if self.identifier:
            d['identifier'] = self.identifier.to_dict()
        else:
            d['identifier'] = None
        return d

    def from_dict(self, d):
        """
        Populates this instances's attributes from the given dictionary
        :param d: dict
        :return: None; updates current instance
        """
        self.id = d.get('id', '')
        self.score = d.get('score', -1.0)
        self.task = d.get('task')
        self.candidate = None
        candidate_dict = d.get('identifier')
        if candidate_dict:
            candidate = SemanticConcept()
            candidate.from_dict(candidate_dict)
            self.identifier = candidate

    def __eq__(self, other):
            if not isinstance(other, LearningVote):
                return False
            elif self.id != other.id:
                return False
            elif self.score != other.score:
                return False
            elif self.task != other.task:
                return False
            elif self.identifier != other.identifier:
                return False
            else:
                return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.id) ^ hash(self.task) ^ hash(self.identifier) ^ hash(self.score) \
               ^ hash((self.id, self.task, self.identifier))
