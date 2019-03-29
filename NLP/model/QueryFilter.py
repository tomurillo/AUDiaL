from NLP.model.Annotation import *

class QueryFilter(object):
    """
    This class models a filtering of labels or results found in a user query
    """
    def __init__(self, annotation=None):
        self.annotation = annotation # Query annotation
        self.operands = []  # List of operands e.g. datatype property value or instance names

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
        return d

    def from_dict(self, d):
        """
        Populates this instances's attributes from the given dictionary
        :param d:
        :return: None; updates current instance
        """
        a_dict = d.get('annotation')
        if a_dict:
            annotation = Annotation()
            self.annotation = annotation.from_dict(a_dict)
        else:
            self.annotation = None
        self.operands = d.get('operands', [])


class QueryFilterNominal(QueryFilter):
    """
    Nominal filtering of graphic elements (i.e. label search)
    """
    def __init__(self, pt):
        super(QueryFilterNominal, self).__init__(pt)

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

    def __init__(self, pt):
        self.op = None  # Operator, one of CardinalFilter
        super(QueryFilterCardinal, self).__init__(pt)

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
        return d

    def from_dict(self, d):
        """
        Populates this instances's attributes from the given dictionary
        :param d:
        :return: None; updates current instance
        """
        super(QueryFilterCardinal, self).from_dict(d)
        self.op = d.get('op')
