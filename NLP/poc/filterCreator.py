from const import *
from NLP.util.TreeUtil import getSubtreesAtHeight, treeRawString
from NLP.model.QueryFilter import *
from GeneralUtil import isNumber


class FilterCreator(object):
    """
    Finds filters in a user's query
    """
    def __init__(self, query):
        """
        FilterCreator class constructor
        :param query: A query instance with POCs and annotations
        """
        self.q = query

    def generateCardinalFilters(self):
        """
        Add cardinal filter instances to the Query
        :return: list<QueryFilter> with found cardinal filters
        """
        filters = []
        for ann in self.q.annotations:
            if ann.tree and ann.tree.label() in FILTER_TOP_LABELS:
                preters = getSubtreesAtHeight(ann.tree, 2)
                qf_operators = []
                qf_operator_combined = None
                operand = None
                or_conj = False
                for pt in preters:
                    if pt.label() in FILTER_COMP_LABELS:
                        parsed_op = self.parseOperator(pt)
                        if parsed_op:
                            qf_operators.append(parsed_op)
                    elif pt.label() in FILTER_OPERAND_LABELS:
                        raw_text = treeRawString(pt)
                        if pt.label() not in FILTER_NUMBER_LABELS or isNumber(raw_text):
                            operand = raw_text
                    elif pt.label() in FILTER_CONJ_LABELS:
                        or_conj = True
                if qf_operators and operand:
                    if or_conj and QueryFilterCardinal.CardinalFilter.EQ in qf_operators:
                        if QueryFilterCardinal.CardinalFilter.GT in qf_operators:
                            qf_operator_combined = QueryFilterCardinal.CardinalFilter.GEQ
                        elif QueryFilterCardinal.CardinalFilter.LT in qf_operators:
                            qf_operator_combined = QueryFilterCardinal.CardinalFilter.LEQ
                    else:
                        qf_operator_combined = qf_operators[0]
                    if qf_operator_combined:
                        qfilter = QueryFilterCardinal(ann, qf_operator_combined)
                        qfilter.operands.append(operand)
                        filters.append(qfilter)
        return filters

    def parseOperator(self, pt):
        """
        Parse a NL operator to a QueryFilterCardinal operand
        :param pt: pre-terminal nltk.Tree parse tree
        :return: string; one of QueryFilterCardinal.CardinalFilter
        """
        qf_operator = None
        operator = treeRawString(pt)
        if operator:
            operator = operator.strip().lower()
            if operator in FILTER_GT_TOKENS:
                qf_operator = QueryFilterCardinal.CardinalFilter.GT
            elif operator in FILTER_LT_TOKENS:
                qf_operator = QueryFilterCardinal.CardinalFilter.LT
            elif operator in FILTER_EQ_TOKENS:
                qf_operator = QueryFilterCardinal.CardinalFilter.EQ
        return qf_operator


