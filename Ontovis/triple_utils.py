from NLP.model.OE import *
from NLP.model.SemanticConcept import *
from NLP.model.Joker import *


def prepareOCsForQuery(scs):
    """
    Given the ontology elements of a consolidated user query, arrange them for generation of search triples in the
    ontology
    :param scs: List<List<SemanticConcept>: overlapped SemanticConcept of the Query
    :return: List<List<SemanticConcept, Joker>: Processed SemanticConcepts with Joker instances added
    """
    scs = arrangeDatatypeProperties(scs)
    scs = arrangeLastProperty(scs)
    scs_with_jokers = addJokersToOEs(scs)
    return scs_with_jokers


def addJokersToOEs(scs):
    """
    Create and position Joker instances where appropriate in a query's OEs list
    :param scs: List<List<SemanticConcept>: overlapped SemanticConcept of the Query
    :return: List<List<SemanticConcept>: Rearranged SemanticConcept with Joker instances added
    """
    oes_with_jokers = []
    if scs and scs[0] and scIsProperty(scs[0][0]):  # Property at the beginning of query, add subject
        joker = Joker(['class', 'instance', 'literal'])
        joker.set_id("first")
        oes_with_jokers.append([joker])
    for i, oe_list in enumerate(scs):
        if oe_list:
            joker = None
            sample = oe_list[0]
            prev_sample = None
            if i > 0 and scs[i-1]:
                prev_sample = scs[i-1][0]
            if scIsConcept(sample) and scIsConcept(prev_sample):  # Two concepts together, add property in between
                joker = Joker(['property'])
            elif scIsProperty(sample) and scIsProperty(prev_sample):  # Two properties together, add concept in between
                joker = Joker(['class', 'literal'])
            if joker:
                oes_with_jokers.append([joker])
            # Add unique identifier for SPARQL generation
            for sc in oe_list:
                sc.set_id(i)
            oes_with_jokers.append(oe_list)
    if scs and scs[-1] and scIsProperty(scs[-1][0]):  # Property at the end of query, add object
        joker = Joker(['class', 'instance', 'literal'])
        joker.set_id("last")
        oes_with_jokers.append([joker])
    return oes_with_jokers


def arrangeDatatypeProperties(scs):
    """
    Rearrange Datatype Property OEs found in a query for triple generation
    :param scs: List<List<SemanticConcept>: overlapped SemanticConcepts of the Query
    :return: List<List<SemanticConcept>: Rearranged SemanticConcepts
    """
    oes_length = len(scs)
    for i, sc_list in enumerate(scs):
        if sc_list and isinstance(sc_list[0].OE, OntologyDatatypePropertyElement) and sc_list[0].OE.governor:
            prev_sc, next_sc = None, None
            if i > 0 and scs[i - 1]:
                prev_sc = scs[i - 1][0]
            if i < oes_length - 1 and scs[i + 1]:
                next_sc = scs[i + 1][0]
            if prev_sc and next_sc and not isinstance(prev_sc.OE, OntologyLiteralElement) and \
                    not isinstance(next_sc.OE, OntologyLiteralElement):
                if next_sc.OE == sc_list[0].OE.governor:
                    scs[i], scs[i+1] = scs[i+1], scs[i]
                elif prev_sc.OE == sc_list[0].OE.governor:
                    scs[i], scs[i-1] = scs[i-1], scs[i]
    return scs


def arrangeLastProperty(scs):
    """
    If the last OE in a query is a property, move it between subject and object OEs
    :param scs: List<List<SemanticConcept>: overlapped SemanticConcepts of the Query
    :return: List<List<SemanticConcept>: Rearranged SemanticConcepts
    """
    if len(scs) > 2 and scIsProperty(scs[-1][0]) and scIsConcept(scs[-2][0]) and scIsConcept(scs[-3][0]):
        scs[-1], scs[-2] = scs[-2], scs[-1]
    return scs


def scIsProperty(sc):
    """
    Returns whether the given SemanticConcept's OE is a (datatype or object) property
    :param sc: SemanticConcept instance
    :return: True if OC is a property; False otherwise
    """
    return isinstance(sc, SemanticConcept) and isinstance(sc.OE, (OntologyObjectPropertyElement,
                                                                  OntologyDatatypePropertyElement))

def scIsDatatypeProperty(sc):
    """
    Returns whether the given SemanticConcept's OE is a datatype property
    :param sc: SemanticConcept instance
    :return: True if OC is a property; False otherwise
    """
    return isinstance(sc, SemanticConcept) and isinstance(sc.OE, OntologyDatatypePropertyElement)

def scIsConcept(sc):
    """
    Returns whether the given SemanticConcept's OE is a concept (i.e. not a property)
    :param sc: SemanticConcept instance
    :return: True if OC is a concept; False otherwise
    """
    return isinstance(sc, SemanticConcept) and isinstance(sc.OE, (OntologyEntityElement,
                                                                  OntologyInstanceElement,
                                                                  OntologyLiteralElement))

def objectIsLiteral(sc):
    """
    Returns whether the given object is a Literal OE or SemanticConcept
    :param sc: Object instance
    :return: True if sc is a SemanticConcept instance with sc.OE a OntologyLiteralElement instance or a
    OntologyLiteralElement instance; False otherwise
    """
    return (isinstance(sc, SemanticConcept) and isinstance(sc.OE, OntologyLiteralElement)) \
        or isinstance(sc, OntologyLiteralElement)


def createSelectSetForDatatypeProperty(sc, prev_sc, next_sc):
    """
    Generates parts of the select set of a SPARQL query when for a Datatype Property
    :param sc: SemanticConcept of a Datatype property instance from a consolidated user query
    :param prev_sc: SemanticConcept Previous OC in the user query or None
    :param next_sc: SemanticConcept Next OC in the user query or None
    :return: string; SPARQL query select set chunk
    """
    sparql = ""
    if sc.task in ['sum', 'avg']:
        choose_prev = False
        if sc.OE.governor and prev_sc and isinstance(next_sc, SemanticConcept) and sc.OE.governor.uri == next_sc.OE.uri:
            choose_prev = True
        elif isinstance(prev_sc, Joker) and isinstance(next_sc, SemanticConcept) \
                and not isinstance(next_sc.OE, OntologyDatatypePropertyElement):
            choose_prev = True
        if choose_prev:
            next_id = prev_sc.id
            prev_sc.answer = True
        else:
            next_id = next_sc.id
            next_sc.answer = True
        if sc.task == 'sum':
            sparql = "select (SUM(xsd:decimal(%s) AS ?JokerElement)" % next_id
        elif sc.task == 'avg':
            sparql = "select (AVG(xsd:decimal%s) AS ?JokerElement)" % next_id
    return sparql


def createWhereSectionForDatatypeProperty(properties, prev_sc, next_sc):
    """
    Generates the where section of a SPARQL query for the given datatype property
    :param properties: List<SemanticConcept> SemanticConcepts for a datatype property of a consolidated query
    :param prev_sc: SemanticConcept; Previous OC in the user query or None
    :param next_sc: SemanticConcept; Next OC in the user query or None
    :return: string; substring of a SPARQL query where section
    """
    sparql = ""
    prop = properties[0] if properties else None
    if isinstance(prop, SemanticConcept) and isinstance(prop.OE, OntologyDatatypePropertyElement):
        gov = prop.OE.governor
        if isinstance(next_sc, SemanticConcept):
            if gov and prev_sc and gov.uri == next_sc.OE.uri:
                subj = next_sc
                obj = prev_sc
            elif isinstance(prev_sc, Joker) and not isinstance(next_sc.OE, OntologyLiteralElement):
                subj = next_sc
                obj = prev_sc
            else:
                subj = prev_sc
                obj = prev_sc
        else:
            subj = prev_sc
            obj = prev_sc
        sparql += " ?%s ?%s ?%s . FILTER (" % (subj.id, prop.id, obj.id)
        num_props = len(properties)
        for i, p in enumerate(properties, 1):
            sparql += " ?%s=<%s> " % (prop.id, p.OE.uri)
            if i < num_props:
                sparql += " || "
        sparql += ") . "
    return sparql


def createOrderSectionForDatatypeProperty(property_sc, prev_sc, next_sc):
    """
    Generates the result order section of a SPARQL query for the given numerical datatype property
    :param property_sc: SemanticConcept instance for a datatype property of a consolidated query
    :param prev_sc: SemanticConcept; Previous OC in the user query or None
    :param next_sc: SemanticConcept; Next OC in the user query or None
    :return: string; substring of a SPARQL query where section
    """
    sparql = ""
    if scIsDatatypeProperty(property_sc) and property_sc.task in ['max', 'min']:
        next_id = ''
        gov = property_sc.OE.governor
        if gov and isinstance(next_sc, SemanticConcept) and prev_sc and gov.uri == next_sc.OE.uri:
            next_id = prev_sc.id
            prev_sc.answer = True
        elif next_sc:
            next_id = next_sc.id
            next_sc.answer = True
        if next_id:
            if property_sc.task == 'max':
                sparql += " DESC("
            else:
                sparql += " ASC("  # Ascending is SPARQL's default ORDER BY operator
            range = ""
            if property_sc.OE.range:
                range = xsdDatatypeForSparqlQuery(property_sc.OE.range[0])
            if range:
                sparql += "%s(" % range
            sparql += "?%s)" % next_id
            if range:
                sparql += ") "
    return sparql


def createWhereUnionSectionForProperty(properties, prev_sc, next_sc):
    """
    Generates the where section of a SPARQL query for the given property occurrence using an union construct. Useful for
    properties whose domain and range are unknown.
    :param properties: List<SemanticConcept> SemanticConcepts for a property of the consolidated query
    :param prev_sc: SemanticConcept; Previous OC in the user query or None
    :param next_sc: SemanticConcept; Next OC in the user query or None
    :return: string; substring of a SPARQL query where section
    """
    sparql = ""
    if properties and prev_sc and next_sc and scIsProperty(properties[0]):
        prop = properties[0]
        sparql += " { { ?%s ?%s ?%s UNION ?%s ?%s ?%s }" % (next_sc.id, prop.id, prev_sc.id,
                                                            prev_sc.id, prop.id, next_sc.id)
        sparql += " . FILTER ("
        num_p = len(properties)
        for i, p in enumerate(properties, 1):
            sparql += "?%s=<%s>" % (prop.id, p.OE.uri)
            if i < num_p:
                sparql += " || "
        sparql += ") } "
    return sparql


def isPropertyReversed(property_sc, prev_sc, next_sc):
    """
    Returns whether this property's subject and object appear in reverse order in a user query
    :param property_sc: SemanticConcept instance of a property of a consolidated query
    :param prev_sc: SemanticConcept; Previous OC in the user query or None
    :param next_sc: SemanticConcept; Next OC in the user query or None
    :return: boolean; True if the property should be reversed; False otherwise
    """
    reverse = False
    if scIsProperty(property_sc):
        prev_uris = []
        if isinstance(prev_sc, SemanticConcept):
            if isinstance(prev_sc.OE, OntologyInstanceElement):
                prev_uris = prev_sc.OE.uris
            elif isinstance(prev_sc.OE, OntologyEntityElement):
                prev_uris = [prev_sc.OE.uri]
        next_uris = []
        if isinstance(next_sc, SemanticConcept):
            if isinstance(next_sc.OE, OntologyInstanceElement):
                next_uris = next_sc.OE.uris
            elif isinstance(next_sc.OE, OntologyEntityElement):
                next_uris = [next_sc.OE.uri]
        range_congruent = True
        domain_congruent = True
        if property_sc.domain and not isinstance(prev_sc, Joker):
            if not any(d in prev_uris for d in property_sc.domain) and any(d in next_uris for d in property_sc.domain):
                domain_congruent = False
        if property_sc.range and not isinstance(next_sc, Joker):
            if not any(r in next_uris for r in property_sc.range) and any(r in prev_uris for r in property_sc.range):
                range_congruent = False
        if (not domain_congruent and not range_congruent) or (not property_sc.domain and not range_congruent) or \
                (not property_sc.range and not domain_congruent):
            reverse = True
    return reverse


def xsdDatatypeForSparqlQuery(lit_type_uri):
    """
    Converts a XSD datatype URI to an equivalent type string to be included in a SPARQL query
    :param lit_type_uri: string; XSD datatype URI
    :return: string; type URI in SPARQL form
    """
    from rdflib import XSD
    ns = getNamespace(lit_type_uri)
    lit = stripNamespace(lit_type_uri)
    sparql = ""
    if ns == str(XSD) or not ns:
        sparql = "xsd:"
        sparql += lit.lower().replace("float", "double")
    else:
        from warnings import warn
        warn('XSD datatype %s contains unknown namespace %s' % (lit_type_uri, ns))
    return sparql


def getNamespace(uri):
    """
    Returns the namespace of the given URI
    :param item: an element's URI
    :return: The namespace part of the URI
    """
    ns = ''
    if uri and '#' in uri:
        return uri.split('#')[0]
    return ns


def stripNamespace(uri):
    """
    Returns the name of the given item without the namespace prefix
    :param uri: an instance's URI
    :return string: resource name without NS prefix
    """
    if uri:
        if '#' in uri:
            return uri.split('#')[1]
        else:
            return str(uri)
    return uri
