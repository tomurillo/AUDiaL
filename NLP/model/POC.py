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
        self.annotation = None
        self.head = ''
        self.start = -1  # Start word offset in query
        self.end = -1  # End word offset in query
        self.start_original = -1  # Copy of start offset in case POC is altered
        self.end_original = -1  # Copy of end offset in case POC is altered
        self.mainSubjectPriority = self.MSUB_PRIORITY_MIN

    def populateFromAnnotation(self, ann):
        """
        Populates this POC's members according to the data from an annotation
        :param ann: Annotation instance
        :return: None
        """
        if ann:
            self.annotation = ann
            self.rawText = ann.rawText
            self.tree = ann.tree
            self.start = ann.start
            self.start_original = ann.start
            self.end = ann.end
            self.end_original = ann.end

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

    def to_dict(self):
        """
        Converts this POC to an equivalent dictionary (of built-in types) representation
        :return: dict
        """
        d = {'tree': str(self.tree), 'rawText': self.rawText, 'head': str(self.head), 'start': self.start,
             'end': self.end, 'start_original': self.start_original, 'end_original': self.end_original,
             'mainSubjectPriority': self.mainSubjectPriority}
        if self.modifiers:
            d['modifiers'] = [str(m) for m in self.modifiers]
        else:
            d['modifiers'] = None
        if self.annotation:
            d['annotation'] = self.annotation.to_dict()
        else:
            d['annotation'] = None
        return d

    def from_dict(self, d):
        """
        Populates this instances's attributes from the given dictionary
        :param d:
        :return: None; updates current instance
        """
        if type(d) is dict:
            from nltk import Tree
            from NLP.model.Annotation import Annotation
            tree = d.get('tree')
            self.tree = Tree.fromstring(tree) if tree else None
            self.rawText = d.get('rawText', '')
            modif = d.get('modifiers', [])
            self.modifiers = [Tree.fromstring(m) for m in modif]
            annotation_dict = d.get('annotation')
            if annotation_dict:
                ann = Annotation()
                ann.from_dict(annotation_dict)
                self.annotation = ann
            else:
                self.annotation = None
            head = d.get('head')
            if head:
                try:
                    self.head = Tree.fromstring(head)
                except ValueError:  # head is a word (string), not a Tree instance
                    self.head = head
            else:
                self.head = None
            self.start = d.get('start', -1)
            self.start_original = d.get('start_original', -1)
            self.end = d.get('end', -1)
            self.end_original = d.get('end_original', -1)
            self.mainSubjectPriority = d.get('mainSubjectPriority', self.MSUB_PRIORITY_MIN)
        else:
            raise ValueError('POC.from_dict: parameter must be of type dict.')

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
        if self.annotation:
            poc_copy.annotation = self.annotation.copy()
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
        if self.annotation:
            poc_copy.annotation = self.annotation.deepcopy()
        if self.modifiers:
            poc_copy.modifiers = [m.copy(deep=True) for m in self.modifiers]
        else:
            poc_copy.modifiers = None
        return poc_copy

    __deepcopy__ = deepcopy
