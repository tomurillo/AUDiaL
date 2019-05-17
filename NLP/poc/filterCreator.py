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
                pos_start, pos_end = len(preters) - 1, 0
                for i, pt in enumerate(preters):
                    match = False
                    if pt.label() in FILTER_COMP_LABELS:
                        parsed_op = self.parseOperator(pt, ann.tree)
                        if parsed_op:
                            qf_operators.append(parsed_op)
                            match = True
                    elif pt.label() in FILTER_OPERAND_LABELS:
                        raw_text = treeRawString(pt)
                        if pt.label() not in FILTER_NUMBER_LABELS or isNumber(raw_text):
                            operand = raw_text
                            match = True
                    elif pt.label() in FILTER_CONJ_LABELS:
                        or_conj = True
                        match = True
                    if match:
                        if i < pos_start:
                            pos_start = i
                        if i > pos_end:
                            pos_end = i
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
                        qfilter.start, qfilter.end = ann.start + pos_start, ann.start + pos_end
                        filters.append(qfilter)
        return filters

    def parseOperator(self, pt, clause_tree):
        """
        Parse a NL operator to a QueryFilterCardinal operand
        :param pt: pre-terminal nltk.Tree parse tree
        :param clause_tree: nltk.Tree instance; parse tree of the full clause where the operator is contained
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
            elif operator in FILTER_GT_THAN_TOKENS or operator in FILTER_LT_THAN_TOKENS:
                clause = treeRawString(clause_tree).strip().lower()
                if " than " in clause:
                    if operator in FILTER_GT_THAN_TOKENS:
                        qf_operator = QueryFilterCardinal.CardinalFilter.GT
                    else:
                        qf_operator = QueryFilterCardinal.CardinalFilter.LT
        return qf_operator
