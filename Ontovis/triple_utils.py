from NLP.model.OE import *
from NLP.model.Joker import *

def prepareOCsForQuery(oes):
    """
    Given the ontology elements of a consolidated user query, arrange them for generation of search triples in the
    ontology
    :param oes: List<List<OntologyElement>: overlapped OntologyElements of the Query
    :return:
    """
    oes = arrangeDatatypeProperties(oes)
    oes = arrangeLastProperty(oes)
    oes_with_jokers = addJokersToOEs(oes)
    

def addJokersToOEs(oes):
    """
    Create and position Joker instances where appropriate in a query's OEs list
    :param oes: List<List<OntologyElement>: overlapped OntologyElements of the Query
    :return: List<List<OntologyElement>: Rearranged OntologyElements with Joker instances added
    """
    oes_with_jokers = []
    if oes and oes[0] and oeIsProperty(oes[0][0]):
        joker = Joker(['class', 'instance', 'literal'])
        oes_with_jokers.append([joker])
    for i, oe_list in enumerate(oes):
        if oe_list:
            joker = None
            sample = oe_list[0]
            prev_sample = None
            if i > 0 and oe_list[i-1]:
                prev_sample = oe_list[i-1][0]
            if oeIsConcept(sample) and oeIsConcept(prev_sample):
                joker = Joker(['property'])
            elif oeIsProperty(sample) and oeIsProperty(prev_sample):
                joker = Joker(['class', 'literal'])
            if joker:
                oes_with_jokers.append([joker])
            oes_with_jokers.append(oe_list)
    if len(oes) > 1 and oes[-1] and oeIsProperty(oes[-1][0]):
        joker = Joker(['class', 'instance', 'literal'])
        oes_with_jokers.append([joker])
    return oes_with_jokers


def arrangeDatatypeProperties(oes):
    """
    Rearrange Datatype Property OEs found in a query for triple generation
    :param oes: List<List<OntologyElement>: overlapped OntologyElements of the Query
    :return: List<List<OntologyElement>: Rearranged OntologyElements
    """
    oes_length = len(oes)
    for i, oe_list in enumerate(oes):
        if oe_list and isinstance(oe_list[0], OntologyDatatypePropertyElement) and oe_list[0].governor:
            prev_oe, next_oe = None, None
            if i > 0 and oes[i - 1]:
                prev_oe = oes[i - 1][0]
            if i < oes_length - 1 and oes[i + 1]:
                next_oe = oes[i + 1][0]
            if prev_oe and next_oe and not isinstance(prev_oe, OntologyLiteralElement) and \
                    not isinstance(next_oe, OntologyLiteralElement):
                if next_oe == oe_list[0].governor:
                    oes[i], oes[i+1] = oes[i+1], oes[i]
                elif prev_oe == oe_list[0].governor:
                    oes[i], oes[i-1] = oes[i-1], oes[i]
    return oes


def arrangeLastProperty(oes):
    """
    If the last OE in a query is a property, move it between subject and object OEs
    :param oes: List<List<OntologyElement>: overlapped OntologyElements of the Query
    :return: List<List<OntologyElement>: Rearranged OntologyElements
    """
    if len(oes) > 2 and oeIsProperty(oes[-1][0]) and oeIsConcept(oes[-2][0]) and oeIsConcept(oes[-3][0]):
        oes[-1], oes[-2] = oes[-2], oes[-1]
    return oes


def oeIsProperty(oe):
    """
    Returns whether the given OE is a proeprty
    :param oe: OntologyElement instance
    :return: True if oe is a property; False otherwise
    """
    return isinstance(oe, (OntologyObjectPropertyElement, OntologyDatatypePropertyElement))


def oeIsConcept(oe):
    """
    Returns whether the given OE is a concept (i.e. not a property)
    :param oe: OntologyElement instance
    :return: True if oe is a concept; False otherwise
    """
    return isinstance(oe, (OntologyEntityElement, OntologyInstanceElement, OntologyLiteralElement))
