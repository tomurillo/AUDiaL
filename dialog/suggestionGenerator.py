from NLP.model.OE import *
from dialog.config import *

class SuggestionGenerator(object):
    """
    Dialogue Suggestions generator
    """

    def __init__(self, ontology, force_parents=True):
        """
        SuggestionGenerator constructor.
        :param ontology: An instantiated ontology
        :param force_parents: whether parent classes/properties should be considered for the suggestions
        :return: None
        """
        self.o = ontology
        self.force_parents = force_parents

    def createVotes(self, key, poc, add_none, skip=None):
        """
        Generate learning votes for the given parameters
        :param key:
        :param poc:
        :param add_none:
        :param skip: list of SemanticConcepts to skip; default None
        :return: list<Vote>
        """
        votes = []
        if skip is None:
            skip = []
        skip_uris = [sc.OE.print_uri() for sc in skip]
        # TODO

        return votes

    def findCandidateElements(self, sc, text):
        """
        Searches for candidate OEs for a clarification dialogue given a Semantic Concept
        :param sc: SemanticConcept instance
        :param text: text from a LearningKey
        :return: list<OntologyElement>: list of candidate OEs to be presented to the user
        """
        candidates = []
        oe = sc.OE
        if oe:
            class_uris = []
            if isinstance(oe, OntologyInstanceElement):
                class_uris.extend(oe.classUris)
            elif isinstance(oe, OntologyEntityElement):
                class_uris.append(oe.uri)
            elif isinstance(oe, OntologyLiteralElement):
                prop_uris = self.findCandidatesForLiteral(oe)
                for p in prop_uris:
                    candidates.append(self.createOntologyElementforURI(p, 'datatypeProperty'))
            elif isinstance(oe, (OntologyObjectPropertyElement, OntologyDatatypePropertyElement)):
                candidates.extend(self.findCandidatesForProperty(oe))
            neighbor_classes = set()
            for uri in class_uris:
                candidate_uris = self.findCandidatesForClass(uri)
                for prop_uri in candidate_uris:
                    candidates.append(self.createOntologyElementforURI(prop_uri, 'property'))
                to_consider = [uri]
                if self.force_parents:
                    to_consider.extend(self.o.getParentClasses(uri, ns=None, stripns=False))
                for c_uri in to_consider:
                    neighbor_classes.update(self.o.neighborRangeOrDomainClasses(c_uri, 'domain', stripns=False))
                    neighbor_classes.update(self.o.neighborRangeOrDomainClasses(c_uri, 'range', stripns=False))
            for neighbor_uri in neighbor_classes:
                candidates.append(self.createOntologyElementforURI(neighbor_uri, 'entity'))
        return list(set(candidates))

    def findCandidatesForClass(self, class_uri):
        """
        Searches for candidates for the given class (properties where the class belongs to their domain or range)
        :param class_uri: string; a Class URI
        :return: list<string>: candidate property URIs
        """
        candidates = []
        classes = [class_uri]
        if self.force_parents:
            classes.extend(self.o.getParentClasses(class_uri, ns=None, stripns=False))
        for c in classes:
            candidates.extend(self.o.propertiesWithRangeOrDomain(c, 'range', stripns=False))
            candidates.extend(self.o.propertiesWithRangeOrDomain(c, 'domain', stripns=False))
        return list(set(candidates))

    def findCandidatesForProperty(self, prop_oe):
        """
        Find candidate suggestions for the given property: properties having the same range or domain; and neighbor
        classes of the classes of its range and domain
        :param prop_oe: OntologyObjectPropertyElement or OntologyDatatypePropertyElement instance
        :return: list<OntologyElement>: list of candidate OEs
        """
        candidates = []
        if isinstance(prop_oe, (OntologyObjectPropertyElement, OntologyDatatypePropertyElement)):
            classes = []
            classes_parents = []
            classes_neighbor = []
            properties = []
            classes.extend(self.o.rangeOfProperty(prop_oe.uri, stripns=False))
            classes.extend(self.o.domainOfProperty(prop_oe.uri, stripns=False))
            if self.force_parents:
                for c in classes:
                    classes_parents.extend(self.o.getParentClasses(c, ns=None, stripns=False))
            classes.extend(classes_parents)
            if len(classes) <= 1 and FORCE_SUGGESTIONS:
                classes.extend(self.o.getClasses(self.o.getNamespace(prop_oe.uri)))
            for class_uri in classes:
                properties.extend(self.o.propertiesWithRangeOrDomain(class_uri, 'domain', stripns=False))
                properties.extend(self.o.propertiesWithRangeOrDomain(class_uri, 'range', stripns=False))
                classes_neighbor.extend(self.o.neighborRangeOrDomainClasses(class_uri, 'domain', stripns=False))
                classes_neighbor.extend(self.o.neighborRangeOrDomainClasses(class_uri, 'range', stripns=False))
            if FORCE_SUGGESTIONS:
                properties.extend(self.o.getProperties(prop_type='all', ns=self.o.getNamespace(prop_oe.uri)))
            for p in properties:
                candidates.append(self.createOntologyElementforURI(p, 'property'))
            for c in classes_neighbor:
                candidates.append(self.createOntologyElementforURI(c, 'entity'))
        return candidates

    def findCandidatesForLiteral(self, literal_oe):
        """
        Find candidate suggestions for the given Literal (candidates of the classes having the Literal as the value
        for one of their datatype properties)
        :param literal_oe: OntologyLiteralElement instance
        :return: list<string>; candidate property URIs
        """
        candidates = []
        if isinstance(literal_oe, OntologyLiteralElement) and literal_oe.triples:
            classes = []
            for s, p, _ in literal_oe.triples:
                if self.o.individualExists(s):
                    classes.extend(self.o.getClassOfElement(s, stripns=False))
                elif self.o.classExists(s):
                    classes.append(s)
            for c in classes:
                candidates.extend(self.findCandidatesForClass(c))
        return candidates

    def createOntologyElementforURI(self, uri, oe_type='any'):
        """
        Given an URI creates an appropriate OntologyElement instance
        :param uri: an element's URI (string)
        :param oe_type: the specific OntologyElement subclass to create. 'Any' to infer it automatically
        :return: an OntologyElement instance (N.B. only its uri property is set); None if the URI does not match an
        element of the given type in the ontology or if it does not exist.
        """
        ns = self.o.getNamespace(uri)
        name = self.o.stripNamespace(uri)
        oe = None
        if oe_type in ['class', 'entity', 'any'] and self.o.classExists(name, ns):
            oe = OntologyEntityElement()
        elif oe_type in ['individual', 'instance', 'any'] and self.o.individualExists(name, ns):
            oe = OntologyInstanceElement()
        elif oe_type in ['objectProperty', 'property', 'any'] and self.o.propertyExists(name, 'objectProperty', ns):
            oe = OntologyObjectPropertyElement()
        elif oe_type in ['datatypeProperty', 'property', 'any'] and self.o.propertyExists(name, 'datatypeProperty', ns):
            oe = OntologyDatatypePropertyElement()
        elif oe_type in ['literal', 'value', 'any'] and self.o.individualExists(name, ns):
            oe = OntologyLiteralElement()
        if oe:
            oe.uri = uri
        return oe
