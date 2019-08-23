"""
Controller configuration constants
"""

# Flask debug mode
FLASK_DEBUG = True

# Bubble HTTP exceptions through the exception stack?
FLASK_BUBBLE_EXCEPTIONS = True

# Which natural language parser should be used; local library ('stanford') or Web service ('stanford_web')
NLP_PARSER = 'stanford_web'

# Which Part-of-Speech tagger should be used; local library ('stanford') or Web service ('stanford_web')
NLP_POS_TAGGER = 'stanford_web'

# Maximum number of nodes (along with any data about them) to output in answers
MAX_OUTPUT_NODES = 15
