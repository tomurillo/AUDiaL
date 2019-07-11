"""
NLP constants file
Most constants are related to POS tags
"""

# ============================================================================= #
#   Penn Treebank II Tags (see https://gist.github.com/nlothian/9240750)
# ============================================================================= #

ROOT_TREE_POS_TAG = 'ROOT'

# Clause Level
S_TREE_POS_TAG = 'S'
SBAR_TREE_POS_TAG = 'SBAR'
SBARQ_TREE_POS_TAG = 'SBARQ'
SINV_TREE_POS_TAG = 'SINV'
SQ_TREE_POS_TAG = 'SQ'

# Phrase Level
ADJP_TREE_POS_TAG = 'ADJP'
ADVP_TREE_POS_TAG = 'ADVP'
CONJP_TREE_POS_TAG = 'CONJP'
FRAG_TREE_POS_TAG = 'FRAG'
INTJ_TREE_POS_TAG = 'INTJ'
LST_TREE_POS_TAG = 'LST'
NAC_TREE_POS_TAG = 'NAC'
NP_TREE_POS_TAG = 'NP'
NX_TREE_POS_TAG = 'NX'
PP_TREE_POS_TAG = 'PP'
PRN_TREE_POS_TAG = 'PRN'
PRT_TREE_POS_TAG = 'PRT'
QP_TREE_POS_TAG = 'QP'
RRC_TREE_POS_TAG = 'RRC'
UCP_TREE_POS_TAG = 'UCP'
VP_TREE_POS_TAG = 'VP'
WHADJP_TREE_POS_TAG = 'WHADJP'
WHADVP_TREE_POS_TAG = 'WHAVDP'
WHAVP_TREE_POS_TAG = 'WHAVP'
WHNP_TREE_POS_TAG = 'WHNP'
WHPP_TREE_POS_TAG = 'WHPP'
X_TREE_POS_TAG = 'X'

# Word Level
CC_TREE_POS_TAG = 'CC'
CD_TREE_POS_TAG = 'CD'
DT_TREE_POS_TAG = 'DT'
EX_TREE_POS_TAG = 'EX'
FW_TREE_POS_TAG = 'FW'
IN_TREE_POS_TAG = 'IN'
JJ_TREE_POS_TAG = 'JJ'
JJR_TREE_POS_TAG = 'JJR'
JJS_TREE_POS_TAG = 'JJS'
LS_TREE_POS_TAG = 'LS'
MD_TREE_POS_TAG = 'MD'
NN_TREE_POS_TAG = 'NN'
NNS_TREE_POS_TAG = 'NNS'
NNP_TREE_POS_TAG = 'NNP'
NNPS_TREE_POS_TAG = 'NNPS'
PDT_TREE_POS_TAG = 'PDT'
POS_TREE_POS_TAG = 'POS'
PRP_TREE_POS_TAG = 'PRP'
PRPDOLLAR_TREE_POS_TAG = 'PRP$'
RB_TREE_POS_TAG = 'RB'
RBR_TREE_POS_TAG = 'RBR'
RBS_TREE_POS_TAG = 'RBS'
SYM_TREE_POS_TAG = 'SYM'
TO_TREE_POS_TAG = 'TO'
UH_TREE_POS_TAG = 'UH'
VB_TREE_POS_TAG = 'VB'
VBD_TREE_POS_TAG = 'CBD'
VBG_TREE_POS_TAG = 'VBG'
VBN_TREE_POS_TAG = 'VBN'
VBP_TREE_POS_TAG = 'VBP'
VBZ_TREE_POS_TAG = 'VBZ'
WDT_TREE_POS_TAG = 'WDT'
WP_TREE_POS_TAG = 'WP'
WPDOLLAR_TREE_POS_TAG = 'WP$'
WRB_TREE_POS_TAG = 'WRB'

# Other
OPEN_QUOTE_TREE_POS_TAG = '``'
CLOSE_QUOTE_TREE_POS_TAG = '\'\''
STERM_TREE_POS_TAG = '.'
COMMA_TREE_POS_TAG = ','
COLON_TREE_POS_TAG = ':'
DOLLAR_TREE_POS_TAG = '$'
POUND_TREE_POS_TAG = '#'

# ================================================== #
#   Part-of-speech main categories
# ================================================== #

POS_TAG_VERB = [VP_TREE_POS_TAG, VB_TREE_POS_TAG, VBD_TREE_POS_TAG, VBG_TREE_POS_TAG, VBN_TREE_POS_TAG, VBP_TREE_POS_TAG,
                VBZ_TREE_POS_TAG]
POS_TAG_ADVB = [ADVP_TREE_POS_TAG, RB_TREE_POS_TAG, RBR_TREE_POS_TAG, RBS_TREE_POS_TAG]
POS_TAG_NOUN = [NP_TREE_POS_TAG, NN_TREE_POS_TAG, NNS_TREE_POS_TAG, NNP_TREE_POS_TAG, NNPS_TREE_POS_TAG]
POS_TAG_JJ = [ADJP_TREE_POS_TAG, JJ_TREE_POS_TAG, JJR_TREE_POS_TAG, JJS_TREE_POS_TAG]

# ================================================== #
#   Helpers
# ================================================== #

# Lemmas not identified by Wordnet lemmatizer
HARD_LEMMA = {'people':'person'}

# Quick synonym search (optional)
QUICK_SYN_NOUN = {'men': 'Male', 'man': 'Male', 'women': 'Female', 'woman': 'Female', 'Wien': 'Vienna'}
