from const import *
from NLP.util.TreeUtil import getSubtreesAtHeight, treeRawString
from NLP.model.QueryFilter import *
from general_util import isNumber


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
            if self.labelOfFilter(ann.tree):
                preters = getSubtreesAtHeight(ann.tree, 2)
                qf_operators = []
                qf_operator_combined = None
                parsed_op = None
                operand = None
                or_conj = False
                negate = False
                pos_start, pos_end = len(preters) - 1, 0
                for i, pt in enumerate(preters):
                    match = False
                    if pt.label() in FILTER_NEG_LABELS:
                        raw_text = treeRawString(pt)
                        if raw_text in FILTER_NEG_TOKENS and not operand and not parsed_op:
                            negate = not negate  # We do not set match=True for overlapsByOperator to work
                    elif pt.label() in FILTER_COMP_LABELS:
                        parsed_op = self.parseOperator(pt, ann.tree)
                        if parsed_op and not operand:
                            qf_operators.append(parsed_op)
                            match = True
                    elif pt.label() in FILTER_OPERAND_LABELS:
                        raw_text = treeRawString(pt)
                        #  Operand must come after operator
                        if qf_operators and not operand and (pt.label() not in FILTER_NUMBER_LABELS or
                                                             isNumber(raw_text)):
                            operand = raw_text
                            match = True
                            pos_end = i
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
                        qfilter = QueryFilterCardinal(ann, qf_operator_combined, negate)
                        qfilter.operands.append(operand)
                        qfilter.start, qfilter.end = ann.start + pos_start, ann.start + pos_end
                        filter_text = ' '.join([treeRawString(t) for t in preters[pos_start: pos_end + 1]])
                        if negate:
                            filter_text = 'not ' + filter_text
                        qfilter.text = filter_text
                        filters.append(qfilter)
        return filters

    def labelOfFilter(self, tree):
        """
        Returns whether the given parse tree may contain a cardinal filter
        :param tree: nltk.Tree instance
        :return: boolean; True if the tree should be considered in cardinal filter search, False otherwise
        """
        potential_filter = False
        if tree:
            if tree.label() in FILTER_TOP_LABELS:
                potential_filter = True
            elif tree.label == NP_TREE_POS_TAG and tree[0].label() == QP_TREE_POS_TAG:  # Quantifier Phrase
                potential_filter = True
        return potential_filter

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
                than_idx = find_substrings(clause, ' than ')
                o_i = clause.find(operator) + len(operator)
                if any(i == o_i for i in than_idx):
                    if operator in FILTER_GT_THAN_TOKENS:
                        qf_operator = QueryFilterCardinal.CardinalFilter.GT
                    else:
                        qf_operator = QueryFilterCardinal.CardinalFilter.LT
            elif operator in FILTER_GEQ_TOKENS:
                clause = treeRawString(clause_tree).strip().lower()
                at_idx = [i + 4 for i in find_substrings(clause, ' at ')]
                if clause[:3] == 'at ':
                    at_idx.append(3)
                o_i = clause.find(operator)
                if any(i == o_i for i in at_idx):
                    qf_operator = QueryFilterCardinal.CardinalFilter.GEQ
        return qf_operator


def find_substrings(main_str, sub_str):
    """
    Return the indices of all occurrences of sub_str in main_str
    :param main_str: string; haystack string where to search for
    :param sub_str: string; needle substring to search for
    :return: list<int> indices where sub_str appears in main_str
    """
    start = 0
    matches = []
    while True:
        start = main_str.find(sub_str, start)
        if start == -1:
            return matches
        matches.append(start)
        start += len(sub_str)
