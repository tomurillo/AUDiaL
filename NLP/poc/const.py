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

FILTER_GT_THAN_TOKENS = ['more', 'higher', 'greater', 'bigger', 'larger', 'older']  # Operators requiring 'than'

FILTER_GT_TOKENS = ['over', 'exceeding', 'after']

FILTER_GEQ_TOKENS = ['least']

FILTER_LT_THAN_TOKENS = ['lower', 'less', 'smaller', 'younger']

FILTER_LT_TOKENS = ['below', 'before']

FILTER_EQ_TOKENS = ['same', 'equal', 'identical', 'exactly']

FILTER_SIM_TOKENS = ['approximate', 'approximately', 'around', 'roughly']

FILTER_CONJ_LABELS = [CC_TREE_POS_TAG]

FILTER_NEG_LABELS = [RB_TREE_POS_TAG, DT_TREE_POS_TAG]

FILTER_NEG_TOKENS = ["n't", "not", "no"]

FILTER_NEG_TOKENS_NOM = ['except ', 'besides ', 'other than ', 'without ', 'excluding ', 'exclude', 'apart from ',
                         'leaving out ', 'leave out ', 'omitting ', 'barring ', 'outside of ', "is n't", "are n't"]

TOKEN_IGNORE_PAIR = ["show me", "give me", "tell me", "show us", "give us", "tell us"]

# Redundant tasks and commands, will be evaluated as filtering tasks if not other task OC found in query
TASK_IGNORE = ["go", "proceed", "move", "show", "give", "tell", "say", "output", "compute", "set", "apply", "get"
               "fetch", "filter", "calculate", "infer", "is", "are", "was", "were", "have", "has", "had", "return",
               "do", "did", "does"]

# Adverbs that can be ignored
RB_IGNORE = ["there", "n't", "not"]
