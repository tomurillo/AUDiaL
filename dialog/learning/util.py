from NLP.model.OE import *


def getGenericElement(element, o):
    """
    Returns the URI of a given element's generic element
    1. If element is a class or property, return the URI of its generic parent class/prop. (if it exists)
    2. If element is an instance, return the URI of its generic class (if it exists)
    3. If element is a literal appearing in a (subject, property, literal) triple, returns
       the generic element of its subject
    4. Otherwise, just return the element's URI
    :param element: an OntologyElement instance
    :param o: Ontology instance
    :return: string; The URI of the generic element; None if not found
    """
    generic = None
    if isinstance(element, OntologyElement):
        if isinstance(element, OntologyEntityElement):
            generic = getGenericElementofClassURI(element.uri, o)
        elif isinstance(element, (OntologyObjectPropertyElement, OntologyDatatypePropertyElement)):
            generic = getGenericElementofPropertyURI(element.uri, o)
        elif isinstance(element, OntologyInstanceElement):
            classes = element.classUris
            if classes:
                max_spec = -1.0
                top_class = None
                for c in classes:
                    specificity = o.specificityOfElement(c)
                    if specificity > max_spec:
                        top_class = c
                        max_spec = specificity
                generic_classes = o.getTopElements(top_class, 'class')
                generic = generic_classes[0] if generic_classes else element.uri
            else:
                generic = element.uri
        elif isinstance(element, OntologyLiteralElement):
            found = False
            if element.triples:
                first_subject = element.triples[0][0]
                if first_subject:
                    generic = getGenericElementofURI(first_subject, o)
                    found = True
            if not found:
                generic = element.uri  # URI actually contains value of Literal
        else:
            generic = element.uri
    return generic


def getGenericElementofURI(element_uri, o):
    """
    Given the URI of an unknown ontology resource, return its generic element URI
    :param element_uri: An URI in the ontology
    :param o: Ontology instance
    :return: string; The URI of the generic element
    """
    generic = None
    ns = o.getNamespace(element_uri)
    name = o.stripNamespace(element_uri)
    if o.classExists(name, ns):
        generic = getGenericElementofClassURI(element_uri, o)
    elif o.propertyExists(name, 'all', ns):
        generic = getGenericElementofPropertyURI(element_uri, o)
    elif o.individualExists(name, ns):
        generic = getGenericElementofIndividualURI(element_uri, o)
    else:
        generic = element_uri
    return generic


def getGenericElementofClassURI(class_uri, o):
    """
    Given the URI of an class, return its generic element URI
    :param class_uri: An URI in the ontology
    :param o: Ontology instance
    :return: string; The URI of the generic element (top-level parent class)
    """
    generic_classes = o.getTopElements(class_uri, 'class')
    return generic_classes[0] if generic_classes else class_uri


def getGenericElementofPropertyURI(prop_uri, o):
    """
    Given the URI of an property, return its generic element URI
    :param prop_uri: An URI in the ontology
    :param o: Ontology instance
    :return: string; The URI of the generic element (top-level parent property)
    """
    generic_props = o.getTopElements(prop_uri, 'property')
    return generic_props[0] if generic_props else prop_uri


def getGenericElementofIndividualURI(ind_uri, o):
    """
    Given the URI of an individual, return its generic element URI (usually a class)
    :param ind_uri: An URI in the ontology
    :param o: Ontology instance
    :return: string; The URI of the generic element
    """
    class_uris = o.getClassOfElement(ind_uri, stripns=False)
    if class_uris:
        max_spec = -1.0
        top_class = None
        for c in class_uris:
            specificity = o.specificityOfElement(c)
            if specificity > max_spec:
                top_class = c
                max_spec = specificity
        generic = getGenericElementofClassURI(top_class, o)
    else:
        generic = ind_uri
    return generic
