from NLP.model.Annotation import *
from NLP.model.SemanticConcept import SemanticConcept
from NLP.model.POC import *
from general_util import stringOpToPython, isNumber


class QueryFilter(object):
    """
    This class models a filtering of labels or results found in a user query
    """
    def __init__(self, annotation=None, negate=False):
        self.annotation = annotation  # Query annotation
        self.text = ''  # Query substring matching the filter
        self.negate = negate  # Whether to negate the result i.e., return elements not meeting filter criteria
        self.operands = []  # List of operands e.g. datatype property value or instance names
        self.pocs = []  # List of POCs found within the filter's annotation
        self.start = -1  # Start offset of actual filter (may be contained within its annotation)
        self.end = -1  # End offset of actual filter

    def overlaps(self, other, strict=True):
        """
        Returns whether the current instance overlaps the given annotation or filter
        :param other: Annotation or QueryFilter instance being compared
        :param strict: whether the containment has to be strict (fully contained) or not (beginning and/or end
        offsets can match)
        :return: boolean; True if current instance overlaps the given one; False otherwise
        """
        overlaps = False
        if isinstance(other, (Annotation, QueryFilter)):
            if strict:
                if other.start > self.start and other.end < self.end:
                    overlaps = True
            else:
                if other.start >= self.start and other.end <= self.end:
                    overlaps = True
        return overlaps

    def to_dict(self):
        """
        Converts this QueryFilter to an equivalent dictionary of builtins
        :return: dict
        """
        d = {'type': 'QueryFilter', 'operands': self.operands, 'negate': self.negate, 'start': self.start,
             'end': self.end, 'text': self.text}
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
        self.text = d.get('text', [])
        self.operands = d.get('operands', [])
        self.negate = d.get('negate', False)
        self.start = d.get('start', -1)
        self.end = d.get('end', -1)
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
        if self.negate != other.negate:
            return False
        elif self.start != other.start:
            return False
        elif self.end != other.end:
            return False
        elif self.text != other.text:
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
        return hash(self.annotation) ^ hash(self.negate) ^ hash(tuple(self.operands)) ^ hash(tuple(self.pocs)) \
               ^ hash(self.start) ^ hash(self.end) ^ hash((self.start, self.end))


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

    def __init__(self, annotation=None, op=None, negate=False):
        self.op = op  # Operator, one of CardinalFilter
        self.property = None  # SemanticConcept instance; property being filtered
        self.result = False  # Whether the filter must be applied to the result rows; only if self.property is None
        self.sim_tol = 10  # Tolerance of SIM filter, in % with respect to the value being compared
        super(QueryFilterCardinal, self).__init__(annotation, negate)

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

    def assertFilter(self, value):
        """
        Returns whether the current filter applies to the given value
        :param value: A numerical value to compare against the filter
        :return: True if value asserts this filter; False otherwise
        """
        ast = False
        if self.op and self.operands and isNumber(value):
            value = float(value)
            if self.op != self.CardinalFilter.SIM:
                op = stringOpToPython(self.opToPython(), self.negate)
                ast = all(op(value, o) for o in self.operands)
            else:
                ast = True
                tol_p = self.sim_tol / 100.0
                for v in self.operands:
                    if isNumber(v):
                        v = float(v)
                        if abs(v) <= 10:
                            upper_tol = v + 1.1
                            lower_tol = v - 1.1
                        else:
                            upper_tol = v * (1 + tol_p)
                            lower_tol = v * (1 - tol_p)
                            if v < 0:
                                upper_tol, lower_tol = lower_tol, upper_tol
                        if value < lower_tol or value > upper_tol:
                            ast = False
                            break
        return ast

    def overlapsByOperator(self, other):
        """
        Returns whether the operator of the current instance overlaps the operator of the given filter. For example,
        the GEQ (>=) operator overlaps the EQ (=) operator.
        :param other: QueryFilter instance being compared
        :return: boolean; True if current instance overlaps the given one; False otherwise
        """
        overlaps = False
        if isinstance(other, QueryFilterCardinal) and self.operands == other.operands:
            if other.op == self.CardinalFilter.EQ and self.op in [self.CardinalFilter.GEQ, self.CardinalFilter.LEQ] \
                    and self.overlaps(other, strict=False):
                overlaps = True
            elif self.start == other.start and self.end == other.end and self.negate and not other.negate:
                overlaps = True
        return overlaps

    def opToPython(self):
        """
        Returns the Python equivalent of this QueryFilter's operator
        :return: string; string operator representation such as '<' or '='
        """
        op = None
        if self.op == self.CardinalFilter.EQ:
            op = '='
        elif self.op == self.CardinalFilter.NEQ:
            op = '!='
        elif self.op == self.CardinalFilter.GT:
            op = '>'
        elif self.op == self.CardinalFilter.GEQ:
            op = '>='
        elif self.op == self.CardinalFilter.LT:
            op = '<'
        elif self.op == self.CardinalFilter.LEQ:
            op = '<='
        elif self.op == self.CardinalFilter.SIM:
            op = '~='
        return op

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
        d['sim_tol'] = self.sim_tol
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
        self.sim_tol = d.get('sim_tol', 10)
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
