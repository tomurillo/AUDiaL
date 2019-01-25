class SemanticConcept(object):
    """
    Semantic Concepts are extended Ontology Concepts (OCs) belonging to a user's query i.e. elements of a query
    that appear in a supporting ontology.
    """
    def __init__(self):
        """
        Semantic Concept constructor
        """
        self.OE = None
        self.verified = False  # Whether this OC has been manually verified in a Disambiguation dialog
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

    def __eq__(self, other):
        if not isinstance(other, SemanticConcept):
            return False
        elif self.verified != other.verified:
            return False
        elif self.task != other.task:
            return False
        elif self.OE != other.OE:
            return False
        else:
            return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.OE) ^ hash(self.verified) ^ hash(self.task)

    def copy(self):
        sc_copy = SemanticConcept()
        sc_copy.OE = self.OE.copy()
        sc_copy.verified = self.verified
        sc_copy.task = self.task
        return sc_copy

    __copy__ = copy

    def deepcopy(self):
        sc_copy = SemanticConcept()
        sc_copy.OE = self.OE.deepcopy()
        sc_copy.verified = self.verified
        sc_copy.task = self.task
        return sc_copy

    __deepcopy__ = deepcopy
