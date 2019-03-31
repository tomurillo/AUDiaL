from dialog.model.SuggestionKey import SuggestionKey
from dialog.model.Vote import Vote
from NLP.model.POC import POC
from NLP.model.QueryFilter import *


class SuggestionPair(object):
    def __init__(self):
        """
        Dialog Suggestion Pair constructor
        """
        self.key = None  # SuggestionKey instance
        self.votes = []  # List of Vote
        self.subject = None  # POC instance
        self.filter = None  # QueryFilter instance

    def to_dict(self):
        """
        Converts this SuggestionPair instance to an equivalent dictionary of builtin types
        :return: dict
        """
        d = {}
        if self.key:
            d['key'] = self.key.to_dict()
        else:
            d['key'] = None
        d['votes'] = [v.to_dict() for v in self.votes] if self.votes else None
        d['subject'] = self.subject.to_dict() if self.subject else None
        d['filter'] = self.filter.to_dict() if self.filter else None
        return d

    def from_dict(self, d):
        """
        Populates this instances's attributes from the given dictionary
        :param d:
        :return: None; updates current instance
        """
        if type(d) is dict:
            key_dict = d.get('key')
            if key_dict:
                key = SuggestionKey()
                key.from_dict(key_dict)
                self.key = key
            else:
                self.key = None
            votes_dict = d.get('votes', [])
            self.votes = []
            for v_dict in votes_dict:
                v = Vote()
                v.from_dict(v_dict)
                self.votes.append(v)
            subject_dict = d.get('subject')
            if subject_dict:
                s = POC()
                s.from_dict(subject_dict)
                self.subject = s
            else:
                self.subject = None
            filter_dict = d.get('filter')
            if filter_dict:
                qf = QueryFilter()
                qf.from_dict(filter_dict)
                self.filter = qf
            else:
                self.filter = None
        else:
            raise ValueError('SuggestionPair.from_dict: parameter must be of type dict.')

    def __eq__(self, other):
            if type(other) is not SuggestionPair:
                return False
            elif self.key != other.key:
                return False
            elif self.votes != other.votes:
                return False
            elif self.subject != other.subject:
                return False
            elif self.filter != other.filter:
                return False
            else:
                return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.key) ^ hash(tuple(self.votes)) ^ hash(self.subject) ^ hash(self.filter)
