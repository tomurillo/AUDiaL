class POC(object):
    """
    Potential Ontology Concept (POC) class
    """

    #  Main Subject Priorities
    MSUB_PRIORITY_MIN = 'min'
    MSUB_PRIORITY_MAX = 'max'

    def __init__(self, rawText='', tree=None):
        """
        POC constructor
        """
        self.tree = tree
        self.rawText = rawText
        self.modifiers = None
        self.head = ''
        self.start = -1  # Start word offset in query
        self.end = -1  # End word offset in query
        self.start_original = -1  # Copy of start offset in case POC is altered
        self.end_original = -1  # Copy of end offset in case POC is altered
        self.mainSubjectPriority = self.MSUB_PRIORITY_MIN

    def copy(self):
        poc_copy = POC()
        if self.tree:
            poc_copy.tree = self.tree.copy()
        else:
            poc_copy.tree = None
        poc_copy.rawText = self.rawText
        poc_copy.start = self.start
        poc_copy.start_original = self.start_original
        poc_copy.end = self.end
        poc_copy.end_original = self.end_original
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
        poc_copy.start_original = self.start_original
        poc_copy.end = self.end
        poc_copy.end_original = self.end_original
        poc_copy.head = self.head
        if self.modifiers:
            poc_copy.modifiers = [m.copy(deep=True) for m in self.modifiers]
        else:
            poc_copy.modifiers = None
        return poc_copy

    __deepcopy__ = deepcopy

    def overlapsOC(self, oc):
        """
        Returns whether this POC overlaps the given Ontology Concept
        :param oc: SemanticConcept instance
        :return: True if the OC's text is contained within the POC's, false otherwise.
        """
        overlaps = False
        if oc and oc.OE.annotation.start >= self.start and oc.OE.annotation.end <= self.end:
            overlaps = True
        return overlaps
