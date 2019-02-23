from NLP.model.OE import *

class SemanticConcept(object):
    """
    Semantic Concepts are extended Ontology Concepts (OCs) belonging to a user's query i.e. elements of a query
    that appear in a supporting ontology.
    """
    def __init__(self):
        """
        Semantic Concept constructor
        """
        self.OE = None  # OntologyElement instance
        self.verified = False  # Whether this OC has been manually verified in a mapping dialog
        self.score = None  # Learning score
        self.task = None  # Maps this OC to an analytical task to be performed

    def overlapsPOC(self, poc):
        """
        Returns whether this Semantic Concept overlaps the given Potential Ontology Concept
        :param poc: POC instance
        :return: True if the POC's text is contained within the SC's, false otherwise.
        """
        overlaps = False
        if poc and poc.start >= self.OE.annotation.start and poc.end <= self.OE.annotation.end:
            overlaps = True
        return overlaps

    def to_dict(self):
        """
        Converts this SemanticConcept to an equivalent dictionary (of built-in types) representation
        :return: dict
        """
        d = {}
        if self.OE:
            d['OE'] = self.OE.to_dict()
        else:
            d['OE'] = None
        d['verified'] = self.verified
        d['score'] = self.score
        d['task'] = self.task
        return d

    def from_dict(self, d):
        """
        Populates this instances's attributes from the given dictionary
        :param d: dict
        :return: None; updates current instance
        """
        self.verified = d.get('verified', False)
        self.score = d.get('score')
        self.task = d.get('task')
        self.OE = None
        oe_dict = d.get('OE')
        if oe_dict:
            oe_type = oe_dict.get('type', 'OntologyElement')
            if oe_type in globals():
                oe_class = globals()[oe_type]
                self.OE = oe_class()
                self.OE.from_dict(oe_dict)

    def __eq__(self, other):
        if not isinstance(other, SemanticConcept):
            return False
        elif self.verified != other.verified:
            return False
        elif self.task != other.task:
            return False
        elif self.score != other.score:
            return False
        elif self.OE != other.OE:
            return False
        else:
            return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.OE) ^ hash(self.verified) ^ hash(self.task) ^ hash(self.score)

    def copy(self):
        sc_copy = SemanticConcept()
        sc_copy.OE = self.OE.copy()
        sc_copy.verified = self.verified
        sc_copy.task = self.task
        sc_copy.score = self.score
        return sc_copy

    __copy__ = copy

    def deepcopy(self):
        sc_copy = SemanticConcept()
        sc_copy.OE = self.OE.deepcopy()
        sc_copy.verified = self.verified
        sc_copy.task = self.task
        sc_copy.score = self.score
        return sc_copy

    __deepcopy__ = deepcopy
