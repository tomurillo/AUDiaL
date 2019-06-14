from NLP.model.Annotation import *


class OntologyElement(object):
    def __init__(self):
        """
        Ontology Element (OE) constructor. An OE is a part of a user query that has an equivalent resource in the
        underlying ontology.
        """
        self.uri = ''  # OE's URI in the ontology
        self.annotation = None  # Associated Query annotation
        self.added = False
        self.main_subject = False

    def print_uri(self):
        """
        Returns this element's URI (for all OEs which do not represent Literals)
        :return: string: this OE's URI
        """
        return self.uri

    def to_dict(self):
        """
        Converts this OntologyElement to an equivalent dictionary (of built-in types) representation
        :return: dict
        """
        d = {'type': 'OntologyElement', 'uri': self.uri, 'added': self.added, 'main_subject': self.main_subject}
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
        self.uri = d.get('uri', '')
        self.added = d.get('added', False)
        self.main_subject = d.get('main_subject', False)
        ann_dict = d.get('annotation')
        if ann_dict:
            self.annotation = Annotation()
            self.annotation.from_dict(ann_dict)
        else:
            self.annotation = None

    def __eq__(self, other):
        if not isinstance(other, OntologyElement):
            return False
        elif str(self.uri) != str(other.uri):
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
        return hash(self.uri) ^ hash(self.added) ^ hash(self.annotation) ^ hash(self.main_subject) \
               ^ hash((self.added, self.main_subject))

    def copy(self):
        oe_copy = OntologyElement()
        oe_copy.added = self.added
        oe_copy.uri = self.uri
        oe_copy.main_subject = self.main_subject
        if self.annotation:
            oe_copy.annotation = self.annotation.copy()
        return oe_copy

    __copy__ = copy

    def deepcopy(self):
        oe_copy = OntologyElement()
        oe_copy.added = self.added
        oe_copy.uri = self.uri
        oe_copy.main_subject = self.main_subject
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
        if not isinstance(other, OntologyEntityElement):
            return False
        elif self.specificity != other.specificity:
            return False
        else:
            return super(OntologyEntityElement, self).__eq__(other)

    def to_dict(self):
        """
        Converts this OntologyEntityElement to an equivalent dictionary (of built-in types) representation
        :return: dict
        """
        d = super(OntologyEntityElement, self).to_dict()
        d['type'] = 'OntologyEntityElement'
        d['specificity'] = self.specificity
        return d

    def from_dict(self, d):
        """
        Populates this instances's attributes from the given dictionary
        :param d:
        :return: None; updates current instance
        """
        super(OntologyEntityElement, self).from_dict(d)
        self.specificity = d.get('specificity', 0)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.uri) ^ hash(self.added) ^ hash(self.annotation) ^ hash(self.specificity) \
               ^ hash(self.main_subject) ^ hash((self.added, self.main_subject))

    def copy(self):
        oe_copy = OntologyEntityElement()
        oe_copy.added = self.added
        oe_copy.uri = self.uri
        oe_copy.main_subject = self.main_subject
        if self.annotation:
            oe_copy.annotation = self.annotation.copy()
        oe_copy.specificity = self.specificity
        return oe_copy

    __copy__ = copy

    def deepcopy(self):
        oe_copy = OntologyEntityElement()
        oe_copy.added = self.added
        oe_copy.uri = self.uri
        oe_copy.main_subject = self.main_subject
        if self.annotation:
            oe_copy.annotation = self.annotation.deepcopy()
        oe_copy.specificity = self.specificity
        return oe_copy

    __deepcopy__ = deepcopy


class OntologyInstanceElement(OntologyElement):
    """
    An ontology element underpinned by one or more ontology instances of the same classes
    """
    def __init__(self):
        self.uris = []  # URIs of instances of the same class(es); this way they are all grouped under the same OE
        self.classUris = []  # URIs of the Classes the instance(s) belongs to
        self.classUri = ''  # URI of the most specific class of the classes of this instance
        super(OntologyInstanceElement, self).__init__()

    def print_uri(self):
        """
        Returns this element's URI
        :return: string: this OE's URI (or URIs if there are several grouped instances under this OE)
        """
        if len(self.uris) > 1:
            return str(self.uris)
        else:
            return super(OntologyInstanceElement, self).print_uri()

    def to_dict(self):
        """
        Converts this OntologyInstanceElement to an equivalent dictionary (of built-in types) representation
        :return: dict
        """
        d = super(OntologyInstanceElement, self).to_dict()
        d['type'] = 'OntologyInstanceElement'
        d['uris'] = self.uris
        d['classUris'] = self.classUris
        d['classUri'] = self.classUri
        return d

    def from_dict(self, d):
        """
        Populates this instances's attributes from the given dictionary
        :param d:
        :return: None; updates current instance
        """
        super(OntologyInstanceElement, self).from_dict(d)
        self.uris = d.get('uris', [])
        self.classUris = d.get('classUris', [])
        self.classUri = d.get('classUri', '')

    def __eq__(self, other):
        if not isinstance(other, OntologyInstanceElement):
            return False
        elif self.classUri != other.classUri:
            return False
        elif set(self.classUris) != set(other.classUris):
            return False
        elif set(self.uris) != set(other.uris):
            return False
        else:
            return super(OntologyInstanceElement, self).__eq__(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.uri) ^ hash(self.classUri) ^ hash(tuple(self.classUris)) ^ hash(tuple(self.uris)) \
               ^ hash(self.added) ^ hash(self.annotation) ^ hash(self.main_subject) \
               ^ hash((self.added, self.main_subject)) ^ hash((self.uri, self.classUri))

    def copy(self):
        oe_copy = OntologyInstanceElement()
        oe_copy.added = self.added
        oe_copy.uri = self.uri
        oe_copy.classUri = self.classUri
        oe_copy.main_subject = self.main_subject
        if self.annotation:
            oe_copy.annotation = self.annotation.copy()
        oe_copy.classUris = self.classUris
        oe_copy.uris = self.uris
        return oe_copy

    __copy__ = copy

    def deepcopy(self):
        oe_copy = OntologyInstanceElement()
        oe_copy.added = self.added
        oe_copy.uri = self.uri
        oe_copy.classUri = self.classUri
        oe_copy.main_subject = self.main_subject
        if self.annotation:
            oe_copy.annotation = self.annotation.deepcopy()
        oe_copy.classUris = list(self.classUris)
        oe_copy.uris = list(self.uris)
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
        self.reversed = False  # Whether subject and object for this OE are reversed in the user query
        super(OntologyObjectPropertyElement, self).__init__()

    def to_dict(self):
        """
        Converts this OntologyObjectPropertyElement to an equivalent dictionary (of built-in types) representation
        :return: dict
        """
        d = super(OntologyObjectPropertyElement, self).to_dict()
        d['type'] = 'OntologyObjectPropertyElement'
        d['domain'] = self.domain
        d['range'] = self.range
        d['specificity_score'] = self.specificity_score
        d['distance_score'] = self.distance_score
        d['reversed'] = self.reversed
        return d

    def from_dict(self, d):
        """
        Populates this instances's attributes from the given dictionary
        :param d:
        :return: None; updates current instance
        """
        super(OntologyObjectPropertyElement, self).from_dict(d)
        self.domain = d.get('domain', [])
        self.range = d.get('range', [])
        self.specificity_score = d.get('specificity_score', 0)
        self.distance_score = d.get('distance_score', 0)
        self.reversed = d.get('reversed', False)

    def __eq__(self, other):
        if not isinstance(other, OntologyObjectPropertyElement):
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
            return super(OntologyObjectPropertyElement, self).__eq__(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.uri) ^ hash(tuple(self.domain)) ^ hash(tuple(self.range)) \
               ^ hash((tuple(self.domain), tuple(self.range))) ^ hash(self.added) ^ hash(self.annotation) \
               ^ hash(self.specificity_score) ^ hash(self.distance_score) \
               ^ hash((self.specificity_score, self.distance_score)) ^ hash(self.main_subject) ^ hash(self.reversed) \
               ^ hash((self.added, self.main_subject, self.reversed))

    def copy(self):
        oe_copy = OntologyObjectPropertyElement()
        oe_copy.added = self.added
        oe_copy.uri = self.uri
        oe_copy.main_subject = self.main_subject
        if self.annotation:
            oe_copy.annotation = self.annotation.copy()
        oe_copy.domain = self.domain
        oe_copy.range = self.range
        oe_copy.specificity_score = self.specificity_score
        oe_copy.distance_score = self.distance_score
        oe_copy.reversed = self.reversed
        return oe_copy

    __copy__ = copy

    def deepcopy(self):
        oe_copy = OntologyObjectPropertyElement()
        oe_copy.added = self.added
        oe_copy.uri = self.uri
        oe_copy.main_subject = self.main_subject
        if self.annotation:
            oe_copy.annotation = self.annotation.deepcopy()
        oe_copy.domain = list(self.domain)
        oe_copy.range = list(self.range)
        oe_copy.specificity_score = self.specificity_score
        oe_copy.distance_score = self.distance_score
        oe_copy.reversed = self.reversed
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
        self.governor = None  # OntologyElement; nearest neighbor of the property in the user query
        self.reversed = False  # Whether subject and object for this OE are reversed in the user query
        super(OntologyDatatypePropertyElement, self).__init__()

    def to_dict(self):
        """
        Converts this OntologyDatatypePropertyElement to an equivalent dictionary (of built-in types) representation
        :return: dict
        """
        d = super(OntologyDatatypePropertyElement, self).to_dict()
        d['type'] = 'OntologyDatatypePropertyElement'
        d['domain'] = self.domain
        d['range'] = self.range
        d['specificity_score'] = self.specificity_score
        d['distance_score'] = self.distance_score
        d['reversed'] = self.reversed
        if self.governor:
            d['governor'] = self.governor.to_dict()
        else:
            d['governor'] = None
        return d

    def from_dict(self, d):
        """
        Populates this instances's attributes from the given dictionary
        :param d:
        :return: None; updates current instance
        """
        super(OntologyDatatypePropertyElement, self).from_dict(d)
        self.domain = d.get('domain', [])
        self.range = d.get('range', [])
        self.specificity_score = d.get('specificity_score', 0)
        self.distance_score = d.get('distance_score', 0)
        self.reversed = d.get('reversed', False)
        self.governor = None
        governor_dict = d.get('governor')
        if governor_dict:
            gov_type = governor_dict.get('type', 'OntologyElement')
            if gov_type in globals():
                gov_class = globals()[gov_type]
                self.governor = gov_class()
                self.governor.from_dict(governor_dict)

    def __eq__(self, other):
        if not isinstance(other, OntologyDatatypePropertyElement):
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
            return super(OntologyDatatypePropertyElement, self).__eq__(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.uri) ^ hash(tuple(self.domain)) ^ hash(tuple(self.range)) \
               ^ hash((tuple(self.domain), tuple(self.range))) ^ hash(self.added) ^ hash(self.annotation) \
               ^ hash(self.specificity_score) ^ hash(self.distance_score) ^ hash(self.reversed) \
               ^ hash((self.specificity_score, self.distance_score)) ^ hash(self.governor) ^ hash(self.main_subject) \
               ^ hash((self.added, self.main_subject, self.reversed))

    def copy(self):
        oe_copy = OntologyDatatypePropertyElement()
        oe_copy.added = self.added
        oe_copy.uri = self.uri
        oe_copy.main_subject = self.main_subject
        if self.annotation:
            oe_copy.annotation = self.annotation.copy()
        if self.governor:
            oe_copy.governor = self.governor.copy()
        oe_copy.domain = self.domain
        oe_copy.range = self.range
        oe_copy.specificity_score = self.specificity_score
        oe_copy.distance_score = self.distance_score
        oe_copy.reversed = self.reversed
        return oe_copy

    __copy__ = copy

    def deepcopy(self):
        oe_copy = OntologyDatatypePropertyElement()
        oe_copy.added = self.added
        oe_copy.uri = self.uri
        oe_copy.main_subject = self.main_subject
        if self.annotation:
            oe_copy.annotation = self.annotation.deepcopy()
        if self.governor:
            oe_copy.governor = self.governor.deepcopy()
        oe_copy.domain = list(self.domain)
        oe_copy.range = list(self.range)
        oe_copy.specificity_score = self.specificity_score
        oe_copy.distance_score = self.distance_score
        oe_copy.reversed = self.reversed
        return oe_copy

    __deepcopy__ = deepcopy


class OntologyLiteralElement(OntologyElement):
    """
    An ontology element underpinned by an ontology literal
    """
    def __init__(self):
        # (SubjectURI, PropertyURI, LiteralURI) triples where this literal appears in the ontology (grouped by property)
        self.triples = []
        super(OntologyLiteralElement, self).__init__()

    def to_dict(self):
        """
        Converts this OntologyLiteralElement to an equivalent dictionary (of built-in types) representation
        :return: dict
        """
        d = super(OntologyLiteralElement, self).to_dict()
        d['type'] = 'OntologyLiteralElement'
        d['triples'] = self.triples
        return d

    def from_dict(self, d):
        """
        Populates this instances's attributes from the given dictionary
        :param d:
        :return: None; updates current instance
        """
        super(OntologyLiteralElement, self).from_dict(d)
        self.triples = d.get('triples', [])

    def print_uri(self):
        """
        Returns this element's triples' URIs
        :return: string: A string representation of this element's triples' URIs
        """
        return str(self.triples)

    def __eq__(self, other):
        if not isinstance(other, OntologyLiteralElement):
            return False
        if self.triples != other.triples:
            return False
        else:
            return super(OntologyLiteralElement, self).__eq__(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.uri) ^ hash(tuple(self.triples)) ^ hash(self.added) ^ hash(self.annotation) \
               ^ hash(self.main_subject) ^ hash((self.added, self.main_subject))

    def copy(self):
        oe_copy = OntologyLiteralElement()
        oe_copy.added = self.added
        oe_copy.uri = self.uri
        oe_copy.main_subject = self.main_subject
        if self.annotation:
            oe_copy.annotation = self.annotation.copy()
        oe_copy.triples = self.triples
        return oe_copy

    __copy__ = copy

    def deepcopy(self):
        oe_copy = OntologyLiteralElement()
        oe_copy.added = self.added
        oe_copy.uri = self.uri
        oe_copy.main_subject = self.main_subject
        if self.annotation:
            oe_copy.annotation = self.annotation.deepcopy()
        oe_copy.triples = list(self.triples)
        return oe_copy

    __deepcopy__ = deepcopy


class OntologyNoneElement(OntologyElement):
    """
    An ontology element not underpinned by any ontology resource
    """
    def __init__(self):
        super(OntologyNoneElement, self).__init__()

    def to_dict(self):
        """
        Converts this OntologyNoneElement to an equivalent dictionary (of built-in types) representation
        :return: dict
        """
        d = super(OntologyNoneElement, self).to_dict()
        d['type'] = 'OntologyNoneElement'
        return d

    def __eq__(self, other):
        if not isinstance(other, OntologyNoneElement):
            return False
        else:
            return super(OntologyNoneElement, self).__eq__(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def copy(self):
        oe_copy = OntologyNoneElement()
        oe_copy.added = self.added
        oe_copy.uri = self.uri
        oe_copy.main_subject = self.main_subject
        if self.annotation:
            oe_copy.annotation = self.annotation.copy()
        return oe_copy

    __copy__ = copy

    def deepcopy(self):
        oe_copy = OntologyNoneElement()
        oe_copy.added = self.added
        oe_copy.uri = self.uri
        oe_copy.main_subject = self.main_subject
        if self.annotation:
            oe_copy.annotation = self.annotation.deepcopy()
        return oe_copy

    __deepcopy__ = deepcopy
