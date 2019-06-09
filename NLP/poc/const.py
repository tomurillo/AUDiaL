"""
POC and filter constants
"""
from NLP.constants import *

FILTER_TOP_LABELS = [PP_TREE_POS_TAG, ADJP_TREE_POS_TAG, QP_TREE_POS_TAG, VP_TREE_POS_TAG, FRAG_TREE_POS_TAG]

FILTER_COMP_LABELS = [JJR_TREE_POS_TAG, RBR_TREE_POS_TAG, JJ_TREE_POS_TAG, IN_TREE_POS_TAG, JJS_TREE_POS_TAG]

FILTER_SUP_LABELS = [JJS_TREE_POS_TAG, RBS_TREE_POS_TAG]

FILTER_OPERAND_LABELS = [CD_TREE_POS_TAG, NNS_TREE_POS_TAG, NNP_TREE_POS_TAG, NNPS_TREE_POS_TAG, NN_TREE_POS_TAG,
                         VBN_TREE_POS_TAG, JJ_TREE_POS_TAG]

# Stanford parser sometimes considers numbers VBN or JJ (?)
FILTER_NUMBER_LABELS = [CD_TREE_POS_TAG, VBN_TREE_POS_TAG, JJ_TREE_POS_TAG]

FILTER_GT_THAN_TOKENS = ['more', 'higher', 'greater', 'bigger', 'larger']  # Operators requiring 'than'

FILTER_GT_TOKENS = ['over', 'exceeding', 'after']

FILTER_GEQ_TOKENS = ['least']

FILTER_LT_THAN_TOKENS = ['lower', 'less', 'smaller']

FILTER_LT_TOKENS = ['below', 'before']

FILTER_EQ_TOKENS = ['same', 'equal', 'identical', 'exactly']

FILTER_SIM_TOKENS = ['approximate', 'approximately', 'about', 'around', 'roughly']

FILTER_CONJ_LABELS = [CC_TREE_POS_TAG]

FILTER_NEG_LABELS = [RB_TREE_POS_TAG, DT_TREE_POS_TAG]

FILTER_NEG_TOKENS = ["n't", "not", "no"]

TOKEN_IGNORE_PAIR = ["show me", "give me", "tell me", "show us", "give us", "tell us"]

# Redundant tasks and commands, will be evaluated as filtering tasks if not other task OC found in query
TASK_IGNORE = ["go", "proceed", "move", "show", "give", "tell", "say", "output", "compute", "set", "apply", "get"
               "fetch", "filter", "calculate", "infer", "is", "are", "was", "were", "have", "has", "had", "return"]

# Adverbs that can be ignored
RB_IGNORE = ["there", "n't", "not"]
