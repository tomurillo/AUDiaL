from NLP.model.OE import *
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
            if i > 0 and oe_list[i-1]:
                prev_sample = oe_list[i-1][0]
            if scIsConcept(sample) and scIsConcept(prev_sample):  # Two concepts together, add property in between
                joker = Joker(['property'])
            elif scIsProperty(sample) and scIsProperty(prev_sample):  # Two properties together, add concept in between
                joker = Joker(['class', 'literal'])
            if joker:
                oes_with_jokers.append([joker])
            # Add unique identifier for SPARQL generation
            for sc in oe_list:
                sc.OE.set_id(i)
            oes_with_jokers.append(oe_list)
    if scs and scs[-1] and scIsProperty(scs[-1][0]):  # Property at the end of query, add object
        joker = Joker(['class', 'instance', 'literal'])
        joker.set_id("last")
        oes_with_jokers.append([joker])
    return oes_with_jokers


def arrangeDatatypeProperties(scs):
    """
    Rearrange Datatype Property OEs found in a query for triple generation
    :param oes: List<List<SemanticConcept>: overlapped SemanticConcepts of the Query
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
    :param oes: List<List<SemanticConcept>: overlapped SemanticConcepts of the Query
    :return: List<List<SemanticConcept>: Rearranged SemanticConcepts
    """
    if len(scs) > 2 and scIsProperty(scs[-1][0]) and scIsConcept(scs[-2][0]) and scIsConcept(scs[-3][0]):
        scs[-1], scs[-2] = scs[-2], scs[-1]
    return scs


def scIsProperty(sc):
    """
    Returns whether the given SemanticConcept's OE is a proeprty
    :param oe: OntologyElement instance
    :return: True if oe is a property; False otherwise
    """
    return sc and sc.OE and isinstance(sc.OE, (OntologyObjectPropertyElement, OntologyDatatypePropertyElement))


def scIsConcept(sc):
    """
    Returns whether the given SemanticConcept's OE is a concept (i.e. not a property)
    :param oe: OntologyElement instance
    :return: True if oe is a concept; False otherwise
    """
    return sc and sc.OE and isinstance(sc.OE, (OntologyEntityElement, OntologyInstanceElement, OntologyLiteralElement))


def createSelectSetForDatatypeProperty(oe, prev_oe, next_oe, task):
    """
    Generates parts of the select set of a SPARQL query when for a Datatype Property
    :param oes: OntologyDatatypePropertyElement instance from a consolidated user query
    :param prev_oe: OntologyElement Previous OE in the user query or None
    :param next_oe: OntologyElement Next OE in the user query or None
    :param task: string; an analytic task the user asked about the property (sum or average)
    :return: string; SPARQL query select set chunk
    """
    sparql = ""
    choose_prev = False
    if oe.governor and prev_oe and next_oe and oe.governor.uri == next_oe.uri:
        choose_prev = True
    elif isinstance(prev_oe, Joker) and not isinstance(next_oe, OntologyDatatypePropertyElement):
        choose_prev = True
    if choose_prev:
        next_id = prev_oe.id
        prev_oe.answer = True
    else:
        next_id = next_oe.id
        next_oe.answer = True
    if task == 'sum':
        sparql = "select (SUM(xsd:decimal(%s) AS ?JokerElement)" % next_id
    elif task == 'avg':
        sparql = "select (AVG(xsd:decimal%s) AS ?JokerElement)" % next_id
    return sparql

