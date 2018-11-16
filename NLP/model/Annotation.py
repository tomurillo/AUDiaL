class Annotation(object):
    def __init__(self, rawText='', tree=None):
        """
        Annotation constructor.
        """
        self.tree = tree  # Must be of type nltk.ImmutableTree
        self.lemma_tree = None
        self.rawText = rawText
        self.start = -1  # Position at which the annotation starts in the sentence
        self.end = -1  # Position at which the annotation ends in the sentence
        self.stem = False  # Whether to lemmatize its text when searching in the KB
        self.inOntology = False  # Does this annotation have an associated OC?
        self.isSynonym = False  # Whether the found OC is a synonym of the annotation
        self.text = ''  # Actual text found in the ontology, if any
        self.oc_type = {}  # Types of ontology concept (class, instance, property, ...) found in the ontology (keys)
                           # and their URIs (vals)
        self.extra = {}  # Extra information e.g. classUri of instance, domain and range of property.

    def __eq__(self, other):
        if type(other) is not Annotation:
            return False
        elif self.start != other.start:
            return False
        elif self.end != other.end:
            return False
        elif self.tree != other.tree:
            return False
        else:
            return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.tree) ^ hash(self.start) ^ hash(self.end) ^ hash((self.start, self.end))

    def copy(self):
        ann_copy = Annotation()
        if self.tree:
            ann_copy.tree = self.tree.copy()
        else:
            ann_copy.tree = None
        if self.lemma_tree:
            ann_copy.lemma_tree = self.lemma_tree.copy()
        else:
            ann_copy.lemma_tree = None
        ann_copy.rawText = self.rawText
        ann_copy.start = self.start
        ann_copy.end = self.end
        ann_copy.stem = self.stem
        ann_copy.inOntology = self.inOntology
        ann_copy.isSynonym = self.isSynonym
        ann_copy.text = self.text
        ann_copy.oc_type = self.oc_type.copy()
        ann_copy.extra = self.extra.copy()
        return ann_copy

    __copy__ = copy

    def deepcopy(self):
        import copy
        ann_copy = Annotation()
        if self.tree:
            ann_copy.tree = self.tree.copy(deep=True)
        else:
            ann_copy.tree = None
        if self.lemma_tree:
            ann_copy.lemma_tree = self.lemma_tree.copy(deep=True)
        else:
            ann_copy.lemma_tree = None
        ann_copy.rawText = self.rawText
        ann_copy.start = self.start
        ann_copy.end = self.end
        ann_copy.stem = self.stem
        ann_copy.inOntology = self.inOntology
        ann_copy.isSynonym = self.isSynonym
        ann_copy.text = self.text
        ann_copy.oc_type = copy.deepcopy(self.oc_type)
        ann_copy.extra = copy.deepcopy(self.extra)
        return ann_copy

    __deepcopy__ = copy

    def equalsNonStrict(self, other):
        """
        Returns whether the current annotation is more or less equal to another one i.e they have the same
        start and end offsets, and the same lowercase text. Their parse trees are ignored.
        :param other: Annotation instance
        :return: Boolean whether both annotations are equal to the text level
        """
        if type(other) is not Annotation:
            return False
        elif self.start != other.start:
            return False
        elif self.end != other.end:
            return False
        elif self.rawText.lower() != other.rawText.lower():
            return False
        else:
            return True

    def overlaps(self, other):
        """
        Returns whether the current annotation overlaps the given one i.e.
        whether the other annotation is strictly contained within the current one
        :param other:
        :return:
        """
        overlaps = False
        if type(other) is Annotation:
            if other.start > self.start and other.end < self.end:
                overlaps = True
        return overlaps
