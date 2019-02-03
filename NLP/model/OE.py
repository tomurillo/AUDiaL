class OntologyElement(object):
    def __init__(self):
        """
        Ontology Element constructor.
        """
        self.uri = ''  # OE's URI in the instance
        self.annotation = None  # Associated Query annotation
        self.added = False

    def print_uri(self):
        """
        Returns this element's URI (for all OEs which do not represent Literals)
        :return: string: this OE's URI
        """
        return self.uri

    def __eq__(self, other):
        if not type(other, OntologyElement):
            return False
        elif self.uri != other.uri:
            return False
        elif self.added != other.added:
            return False
        elif self.annotation != other.annotation:
            return False
        else:
            return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.uri) ^ hash(self.added) ^ hash(self.annotation)

    def copy(self):
        oe_copy = OntologyElement()
        oe_copy.added = self.added
        oe_copy.uri = self.uri
        if self.annotation:
            oe_copy.annotation = self.annotation.copy()
        return oe_copy

    __copy__ = copy

    def deepcopy(self):
        oe_copy = OntologyElement()
        oe_copy.added = self.added
        oe_copy.uri = self.uri
        if self.annotation:
            oe_copy.annotation = self.annotation.deepcopy()
        return oe_copy

    __deepcopy__ = deepcopy


class OntologyEntityElement(OntologyElement):
    """
    An ontology element underpinned by an ontology Class
    """
    def __init__(self):
        self.specificity = 0  # Specificity distance
        super(OntologyEntityElement, self).__init__()

    def __eq__(self, other):
        if not type(other, OntologyEntityElement):
            return False
        elif self.specificity != other.specificity:
            return False
        else:
            super(OntologyEntityElement, self).__eq__(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.uri) ^ hash(self.added) ^ hash(self.annotation) ^ hash(self.specificity)

    def copy(self):
        oe_copy = OntologyEntityElement()
        oe_copy.added = self.added
        oe_copy.uri = self.uri
        if self.annotation:
            oe_copy.annotation = self.annotation.copy()
        oe_copy.specificity = self.specificity
        return oe_copy

    __copy__ = copy

    def deepcopy(self):
        oe_copy = OntologyEntityElement()
        oe_copy.added = self.added
        oe_copy.uri = self.uri
        if self.annotation:
            oe_copy.annotation = self.annotation.deepcopy()
        oe_copy.specificity = self.specificity
        return oe_copy

    __deepcopy__ = deepcopy


class OntologyInstanceElement(OntologyElement):
    """
    An ontology element underpinned by an ontology instance
    """
    def __init__(self):
        self.classUris = []  # URIs of the Classes the instance belongs to
        super(OntologyInstanceElement, self).__init__()

    def __eq__(self, other):
        if not type(other, OntologyInstanceElement):
            return False
        elif set(self.classUris) != set(other.classUris):
            return False
        else:
            super(OntologyInstanceElement, self).__eq__(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.uri) ^ hash(tuple(self.classUris)) ^ hash(self.added) ^ hash(self.annotation)

    def copy(self):
        oe_copy = OntologyInstanceElement()
        oe_copy.added = self.added
        oe_copy.uri = self.uri
        if self.annotation:
            oe_copy.annotation = self.annotation.copy()
        oe_copy.classUris = self.classUris
        return oe_copy

    __copy__ = copy

    def deepcopy(self):
        oe_copy = OntologyInstanceElement()
        oe_copy.added = self.added
        oe_copy.uri = self.uri
        if self.annotation:
            oe_copy.annotation = self.annotation.deepcopy()
        oe_copy.classUris = list(self.classUris)
        return oe_copy

    __deepcopy__ = deepcopy


class OntologyObjectPropertyElement(OntologyElement):
    """
    An ontology element underpinned by an ontology object property
    """
    def __init__(self):
        self.domain = []  # Domain of property
        self.range = []  # Range of property
        self.specificity_score = 0
        self.distance_score = 0
        super(OntologyObjectPropertyElement, self).__init__()

    def __eq__(self, other):
        if not type(other, OntologyObjectPropertyElement):
            return False
        elif set(self.domain) != set(other.domain):
            return False
        elif set(self.range) != set(other.range):
            return False
        elif self.specificity_score != other.specificity_score:
            return False
        elif self.distance_score != other.distance_score:
            return False
        else:
            super(OntologyObjectPropertyElement, self).__eq__(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.uri) ^ hash(tuple(self.domain)) ^ hash(tuple(self.range)) \
               ^ hash((tuple(self.domain), tuple(self.range))) ^ hash(self.added) ^ hash(self.annotation) \
               ^ hash(self.specificity_score) ^ hash(self.distance_score) \
               ^ hash((self.specificity_score, self.distance_score))

    def copy(self):
        oe_copy = OntologyObjectPropertyElement()
        oe_copy.added = self.added
        oe_copy.uri = self.uri
        if self.annotation:
            oe_copy.annotation = self.annotation.copy()
        oe_copy.domain = self.domain
        oe_copy.range = self.range
        oe_copy.specificity_score = self.specificity_score
        oe_copy.distance_score = self.distance_score
        return oe_copy

    __copy__ = copy

    def deepcopy(self):
        oe_copy = OntologyObjectPropertyElement()
        oe_copy.added = self.added
        oe_copy.uri = self.uri
        if self.annotation:
            oe_copy.annotation = self.annotation.deepcopy()
        oe_copy.domain = list(self.domain)
        oe_copy.range = list(self.range)
        oe_copy.specificity_score = self.specificity_score
        oe_copy.distance_score = self.distance_score
        return oe_copy

    __deepcopy__ = deepcopy


class OntologyDatatypePropertyElement(OntologyElement):
    """
    An ontology element underpinned by an ontology datatype property
    """
    def __init__(self):
        self.domain = []  # Domain of property
        self.range = []  # Range of property
        self.specificity_score = 0
        self.distance_score = 0
        self.governor = None  # OntologyElement instance from its domain
        super(OntologyDatatypePropertyElement, self).__init__()

    def __eq__(self, other):
        if not type(other, OntologyDatatypePropertyElement):
            return False
        elif set(self.domain) != set(other.domain):
            return False
        elif set(self.range) != set(other.range):
            return False
        elif self.specificity_score != other.specificity_score:
            return False
        elif self.distance_score != other.distance_score:
            return False
        elif self.governor != other.governor:
            return False
        else:
            super(OntologyDatatypePropertyElement, self).__eq__(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.uri) ^ hash(tuple(self.domain)) ^ hash(tuple(self.range)) \
               ^ hash((tuple(self.domain), tuple(self.range))) ^ hash(self.added) ^ hash(self.annotation) \
               ^ hash(self.specificity_score) ^ hash(self.distance_score) \
               ^ hash((self.specificity_score, self.distance_score)) ^ hash(self.governor)

    def copy(self):
        oe_copy = OntologyDatatypePropertyElement()
        oe_copy.added = self.added
        oe_copy.uri = self.uri
        if self.annotation:
            oe_copy.annotation = self.annotation.copy()
        if self.governor:
            oe_copy.governor = self.governor.copy()
        oe_copy.domain = self.domain
        oe_copy.range = self.range
        oe_copy.specificity_score = self.specificity_score
        oe_copy.distance_score = self.distance_score
        return oe_copy

    __copy__ = copy

    def deepcopy(self):
        oe_copy = OntologyDatatypePropertyElement()
        oe_copy.added = self.added
        oe_copy.uri = self.uri
        if self.annotation:
            oe_copy.annotation = self.annotation.deepcopy()
        if self.governor:
            oe_copy.governor = self.governor.deepcopy()
        oe_copy.domain = list(self.domain)
        oe_copy.range = list(self.range)
        oe_copy.specificity_score = self.specificity_score
        oe_copy.distance_score = self.distance_score
        return oe_copy

    __deepcopy__ = deepcopy


class OntologyLiteralElement(OntologyElement):
    """
    An ontology element underpinned by an ontology literal
    """
    def __init__(self):
        self.triples = []  # (SubjectURI, PropertyURI, LiteralURI) triples where this literal appears in the ontology
        super(OntologyLiteralElement, self).__init__()

    def print_uri(self):
        """
        Returns this element's triples' URIs
        :return: string: A string representation of this element's triples' URIs
        """
        return str(self.triples)

    def __eq__(self, other):
        if not type(other, OntologyLiteralElement):
            return False
        if self.triples != other.triples:
            return False
        else:
            super(OntologyLiteralElement, self).__eq__(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.uri) ^ hash(tuple(self.triples)) ^ hash(self.added) ^ hash(self.annotation)

    def copy(self):
        oe_copy = OntologyLiteralElement()
        oe_copy.added = self.added
        oe_copy.uri = self.uri
        if self.annotation:
            oe_copy.annotation = self.annotation.copy()
        oe_copy.triples = self.triples
        return oe_copy

    __copy__ = copy

    def deepcopy(self):
        oe_copy = OntologyLiteralElement()
        oe_copy.added = self.added
        oe_copy.uri = self.uri
        if self.annotation:
            oe_copy.annotation = self.annotation.deepcopy()
        oe_copy.triples = list(self.triples)
        return oe_copy

    __deepcopy__ = deepcopy


class OntologyNoneElement(OntologyElement):
    """
    An ontology element not underpinned by any ontological element
    """
    def __init__(self):
        super(OntologyNoneElement, self).__init__()

    def __eq__(self, other):
        if not type(other, OntologyNoneElement):
            return False
        else:
            super(OntologyNoneElement, self).__eq__(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def copy(self):
        oe_copy = OntologyNoneElement()
        oe_copy.added = self.added
        oe_copy.uri = self.uri
        if self.annotation:
            oe_copy.annotation = self.annotation.copy()
        return oe_copy

    __copy__ = copy

    def deepcopy(self):
        oe_copy = OntologyNoneElement()
        oe_copy.added = self.added
        oe_copy.uri = self.uri
        if self.annotation:
            oe_copy.annotation = self.annotation.deepcopy()
        return oe_copy

    __deepcopy__ = deepcopy
