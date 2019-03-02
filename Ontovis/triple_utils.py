from NLP.model.OE import *

def prepareOCsForQuery(oes):
    """
    Given the ontology elements of a consolidated user query, arrange them for generation of search triples in the
    ontology
    :param oes: List<List<OntologyElement>: overlapped OntologyElements of the Query
    :return:
    """
    pass


def arrangeDatatypeProperties(oes):
    """
    Rearrange OntologyDatatypePropertyElements for triple generation
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
