from NLP.model.Annotation import *
from NLP.model.SemanticConcept import SemanticConcept
from NLP.model.POC import *


class QueryFilter(object):
    """
    This class models a filtering of labels or results found in a user query
    """
    def __init__(self, annotation=None):
        self.annotation = annotation  # Query annotation
        self.operands = []  # List of operands e.g. datatype property value or instance names
        self.pocs = []  # List of POCs found within the filter's annotation

    def to_dict(self):
        """
        Converts this QueryFilter to an equivalent dictionary of builtins
        :return: dict
        """
        d = {'type': 'QueryFilter', 'operands': self.operands}
        if self.annotation:
            d['annotation'] = self.annotation.to_dict()
        else:
            d['annotation'] = None
        d['pocs'] = [poc.to_dict() for poc in self.pocs]
        return d

    def from_dict(self, d):
        """
        Populates this instances's attributes from the given dictionary
        :param d:
        :return: None; updates current instance
        """
        self.operands = d.get('operands', [])
        a_dict = d.get('annotation')
        if a_dict:
            annotation = Annotation()
            annotation.from_dict(a_dict)
            self.annotation = annotation
        else:
            self.annotation = None
        self.pocs = []
        pocs_dict = d.get('pocs')
        if pocs_dict:
            for poc_dict in pocs_dict:
                poc = POC()
                poc.from_dict(poc_dict)
                self.pocs.append(poc)

    def __eq__(self, other):
        if not isinstance(other, QueryFilter):
            return False
        elif other.annotation != self.annotation:
            return False
        elif set(other.operands) != set(self.operands):
            return False
        else:
            return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.annotation) ^ hash(tuple(self.operands)) ^ hash(tuple(self.pocs))


class QueryFilterNominal(QueryFilter):
    """
    Nominal filtering of graphic elements (i.e. label search)
    """
    def __init__(self, annotation):
        super(QueryFilterNominal, self).__init__(annotation)

    def to_dict(self):
        """
        Converts this QueryFilterNominal to an equivalent dictionary of builtins
        :return: dict
        """
        d = super(QueryFilterNominal, self).to_dict()
        d['type'] = 'QueryFilterNominal'
        return d

    def from_dict(self, d):
        """
        Populates this instances's attributes from the given dictionary
        :param d:
        :return: None; updates current instance
        """
        super(QueryFilterNominal, self).from_dict(d)


class QueryFilterCardinal(QueryFilter):
    """
    Cardinal filtering of datatype property values
    """

    def __init__(self, annotation=None, op=None):
        self.op = op  # Operator, one of CardinalFilter
        self.property = None  # SemanticConcept instance; property being filtered
        self.result = False  # Whether the filter must be applied to the result rows; only if self.property is None
        super(QueryFilterCardinal, self).__init__(annotation)

    class CardinalFilter:
        """
        Enumeration of literal cardinal filters
        """
        EQ = "equal"
        NEQ = "distinct"
        GT = "greater_than"
        GEQ = "greater_equal_than"
        LT = "less_than"
        LEQ = "less_equal_than"
        SIM = 'similar_to'

    def to_dict(self):
        """
        Converts this QueryFilterNominal to an equivalent dictionary of builtins
        :return: dict
        """
        d = super(QueryFilterCardinal, self).to_dict()
        d['type'] = 'QueryFilterCardinal'
        d['op'] = self.op
        d['property'] = self.property.to_dict() if self.property else None
        d['result'] = self.result
        return d

    def from_dict(self, d):
        """
        Populates this instances's attributes from the given dictionary
        :param d:
        :return: None; updates current instance
        """
        super(QueryFilterCardinal, self).from_dict(d)
        self.op = d.get('op')
        self.result = d.get('result', False)
        prop_dict = d.get('property')
        if prop_dict:
            self.property = SemanticConcept()
            self.property.from_dict(prop_dict)
        else:
            self.property = None

    def __eq__(self, other):
        if type(other) is not QueryFilterCardinal:
            return False
        elif other.op != self.op:
            return False
        elif other.result != self.result:
            return False
        elif other.property != self.property:
            return False
        else:
            return super(QueryFilterCardinal, self).__eq__(other)

    def __ne__(self, other):
        return not self.__eq__(other)
