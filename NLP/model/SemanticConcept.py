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
        self.answer = False  # Whether this OC is the query's answer
        self.score = None  # Learning score
        self.task = None  # Maps this OC to an analytical task to be performed
        self.id = ''  # Unique identifier for SPARQL generation (variable used in SPARQL query)

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

    def set_id(self, n):
        """
        Sets this instance's id attribute
        :param n: int; position of this element within a OC list
        :return: None; updates this instance
        """
        sql_id = ""
        try:
            if isinstance(self.OE, OntologyEntityElement):
                sql_id = 'c%d' % n
            elif isinstance(self.OE, OntologyInstanceElement):
                sql_id = 'i%d' % n
            elif isinstance(self.OE, OntologyObjectPropertyElement):
                sql_id = 'op%d' % n
            elif isinstance(self.OE, OntologyDatatypePropertyElement):
                sql_id = 'dp%d' % n
            elif isinstance(self.OE, OntologyLiteralElement):
                sql_id = 'd%d' % n
        except ValueError:
            from warnings import warn
            warn("SemanticConcept ID has been set to a non-numerical value", SyntaxWarning)
            sql_id = "e%s" % n
        finally:
            self.id = sql_id

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
        d['id'] = self.id
        d['verified'] = self.verified
        d['answer'] = self.answer
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
        self.answer = d.get('answer', False)
        self.score = d.get('score')
        self.task = d.get('task')
        self.id = d.get('id', '')
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
        elif self.answer != other.answer:
            return False
        elif self.task != other.task:
            return False
        elif self.score != other.score:
            return False
        elif self.id != other.id:
            return False
        elif self.OE != other.OE:
            return False
        else:
            return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.OE) ^ hash(self.verified) ^ hash(self.task) ^ hash(self.score) ^ hash(self.id) \
               ^ hash(self.answer) ^ hash((self.task, self.score)) ^ hash((self.answer, self.verified))

    def copy(self):
        sc_copy = SemanticConcept()
        sc_copy.OE = self.OE.copy()
        sc_copy.verified = self.verified
        sc_copy.task = self.task
        sc_copy.score = self.score
        sc_copy.id = self.id
        sc_copy.answer = self.answer
        return sc_copy

    __copy__ = copy

    def deepcopy(self):
        sc_copy = SemanticConcept()
        sc_copy.OE = self.OE.deepcopy()
        sc_copy.verified = self.verified
        sc_copy.task = self.task
        sc_copy.score = self.score
        sc_copy.id = self.id
        sc_copy.answer = self.answer
        return sc_copy

    __deepcopy__ = deepcopy
