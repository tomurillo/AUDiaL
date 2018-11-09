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
