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

    def copy(self):
        poc_copy = POC()
        if self.tree:
            poc_copy.tree = self.tree.copy()
        else:
            poc_copy.tree = None
        poc_copy.rawText = self.rawText
        poc_copy.start = self.start
        poc_copy.end = self.end
        poc_copy.head = self.head
        if self.modifiers:
            poc_copy.modifiers = [m.copy() for m in self.modifiers]
        else:
            poc_copy.modifiers = None
        return poc_copy

    __copy__ = copy

    def deepcopy(self):
        poc_copy = POC()
        if self.tree:
            poc_copy.tree = self.tree.copy(deep=True)
        else:
            poc_copy.tree = None
        poc_copy.rawText = self.rawText
        poc_copy.start = self.start
        poc_copy.end = self.end
        poc_copy.head = self.head
        if self.modifiers:
            poc_copy.modifiers = [m.copy(deep=True) for m in self.modifiers]
        else:
            poc_copy.modifiers = None
        return poc_copy

    __deepcopy__ = copy
