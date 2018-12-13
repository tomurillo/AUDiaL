class OntologyElement(object):
    def __init__(self):
        """
        Ontology Element constructor.
        """
        self.uri = ''  # OE's URI in the instance
        self.annotation = None  # Associated Query annotation
        self.added = False

    def __eq__(self, other):
        if not isinstance(other, OntologyElement):
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


class OntologyEntityElement(OntologyElement):
    """
    An ontology element underpinned by an ontology Class
    """
    def __init__(self):
        super(OntologyEntityElement, self).__init__()

    def __eq__(self, other):
        if not type(other, OntologyEntityElement):
            return False
        else:
            super(OntologyEntityElement, self).__eq__(other)

    def __ne__(self, other):
        return not self.__eq__(other)


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


class OntologyObjectPropertyElement(OntologyElement):
    """
    An ontology element underpinned by an ontology object property
    """
    def __init__(self):
        self.domain = []  # Domain of property
        self.range = []  # Range of property
        super(OntologyObjectPropertyElement, self).__init__()

    def __eq__(self, other):
        if not type(other, OntologyObjectPropertyElement):
            return False
        elif set(self.domain) != set(other.domain):
            return False
        elif set(self.range) != set(other.range):
            return False
        else:
            super(OntologyObjectPropertyElement, self).__eq__(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.uri) ^ hash(tuple(self.domain)) ^ hash(tuple(self.range)) \
               ^ hash((tuple(self.domain), tuple(self.range))) ^ hash(self.added) ^ hash(self.annotation)


class OntologyDatatypePropertyElement(OntologyElement):
    """
    An ontology element underpinned by an ontology datatype property
    """
    def __init__(self):
        self.domain = []  # Domain of property
        self.range = []  # Range of property
        super(OntologyDatatypePropertyElement, self).__init__()

    def __eq__(self, other):
        if not type(other, OntologyDatatypePropertyElement):
            return False
        elif set(self.domain) != set(other.domain):
            return False
        elif set(self.range) != set(other.range):
            return False
        else:
            super(OntologyDatatypePropertyElement, self).__eq__(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.uri) ^ hash(tuple(self.domain)) ^ hash(tuple(self.range)) \
               ^ hash((tuple(self.domain), tuple(self.range))) ^ hash(self.added) ^ hash(self.annotation)


class OntologyLiteralElement(OntologyElement):
    """
    An ontology element underpinned by an ontology literal
    """
    def __init__(self):
        self.triples = []  # (Subject, Property, Literal) triples where this literal appears in the ontology
        super(OntologyLiteralElement, self).__init__()

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
