"""
POC and filter constants
"""
from NLP.constants import *

FILTER_TOP_LABELS = [PP_TREE_POS_TAG, ADJP_TREE_POS_TAG]

FILTER_COMP_LABELS = [JJR_TREE_POS_TAG, RBR_TREE_POS_TAG, JJ_TREE_POS_TAG, IN_TREE_POS_TAG]

FILTER_SUP_LABELS = [JJS_TREE_POS_TAG, RBS_TREE_POS_TAG]

FILTER_OPERAND_LABELS = [CD_TREE_POS_TAG, NNP_TREE_POS_TAG, NNPS_TREE_POS_TAG, NN_TREE_POS_TAG, NNS_TREE_POS_TAG]

FILTER_GT_TOKENS = ['more', 'higher', 'greater', 'bigger', 'larger', 'over', 'exceeding']

FILTER_LT_TOKENS = ['lower', 'less', 'smaller', 'below']

FILTER_EQ_TOKENS = ['same', 'equal', 'identical', 'exactly']

FILTER_CONJ_LABELS = [CC_TREE_POS_TAG]


TOKEN_IGNORE_PAIR = ["show me", "give me", "tell me", "show us", "give us", "tell us"]

# Redundant tasks and commands, will be evaluated as filtering tasks if not other task OC found in query
TASK_IGNORE = ["go", "proceed", "move", "show", "give", "tell", "say", "output", "compute", "set", "apply", "get"
               "fetch", "filter", "calculate", "infer", "is", "are", "was", "were", "have", "has", "had"]

# Adverbs that can be ignored
RB_IGNORE = ["there"]
