"""
Controller configuration constants
"""

#  Flask App secret key. Keep this secret in production environments!
FLASK_SECRET_KEY = u'l\x04\x8a\x01T\xbb\xb5P4\x88h\xc2\x02\x0c\xe7|'

# Flask App debug mode
FLASK_DEBUG = True

# Flask App exception propagation and bubbling
FLASK_BUBBLE_EXCEPTIONS = True

# Which natural language parser should be used; local library ('stanford') or Web service ('stanford_web')
NLP_PARSER = 'stanford_web'

# Which Part-of-Speech tagger should be used; local library ('stanford') or Web service ('stanford_web')
NLP_POS_TAGGER = 'stanford_web'
