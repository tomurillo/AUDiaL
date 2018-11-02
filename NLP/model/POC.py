class POC(object):
    def __init__(self, rawText, tree):
        """
        POC (Potential Ontology Concept) constructor
        """
        self.tree = tree
        self.rawText = rawText
        self.modifiers = None
        self.head = ''
        self.start = -1  # Start offset in query
        self.end = -1  # End offset in query
