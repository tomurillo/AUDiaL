from NLP.model.Query import Query
from NLP.model.FormalQuery import *
from NLP.model.Joker import *
from Ontovis.upper_ontology import UpperOntology
from dialog.webformat.formatter import OutputFormatter


def generateAnswer(query, formal_query, query_result, o):
    """
    Creates an answer to be displayed to the user once a query has been resolved
    :param query: Resolved Query instance
    :param formal_query: FormalQuery instance that generated the results
    :param query_result: List<ResultRow>: the results from executing the formal query
    :param o: Ontology instance
    :return: string
    """
    answer = ""
    if isinstance(query, Query) and isinstance(formal_query, FormalQuery) and isinstance(o, UpperOntology):
        import inflect
        p = inflect.engine()
        formatter = OutputFormatter(o)
        sample = query.answerType[0] if query.answerType else None
        n_rows = len(query_result)
        answered = False
        if isinstance(sample, OntologyElement):
            if isinstance(sample, OntologyEntityElement):  # Answer type is class: list instances as answer
                answered = True
                instances = o.getInstances(sample.uri, stripns=False)
                n_rows = len(instances)
                class_label = formatter.quickURILabel(sample.uri)
                answer = "There %s %s" % (p.plural_verb("is", n_rows), p.no(class_label, n_rows))
                if n_rows > 0:
                    answer += ":"
                for n, i in enumerate(instances, 1):
                    answer += "\t%d: %s\n" % (n, formatter.printLabelsOfUri(i))
            elif isinstance(sample, OntologyDatatypePropertyElement):  # AT is datatype property: list occurrences
                if n_rows == 0:  # If we got rows fetch answer from them instead
                    answered = True
                    prop_label = formatter.quickURILabel(sample.uri, 'datatypeProperty')
                    occurrences = o.getOccurrences(sample, stripns=False)
                    n_rows = len(occurrences)
                    answer = "There %s %s for %s" % (p.plural_verb("is", n_rows), p.no("value", n_rows), prop_label)
                    if n_rows > 0:
                        answer += ":"
                    for n, triple in enumerate(occurrences, 1):
                        i = formatter.printLabelsOfUri(triple[0])
                        v = formatter.quickURILabel(triple[2])
                        if n_rows > 1:
                            answer += "\t%d: %s %s %s\n" % (n, i, prop_label, v)
                        else:
                            answer += "%s %s %s\n" % (i, prop_label, v)
        if not answered:
            for n, triple in enumerate(query_result, 1):
                triple_answer = printAnswerTriple(triple, formal_query, formatter, o)
                if n_rows > 1:
                    answer += "\t%d: %s\n" % (n, triple_answer)
                else:
                    answer += "%s\n" % triple_answer
    return answer


def printAnswerTriple(triple, formal_query, formatter, o=None):
    """
    Given a formal result triple prints a human-readable version thereof
    :param triple: ResultRow instance
    :param formal_query: FormalQuery instance
    :param formatter: OutputFormatter instance
    :param o: UpperOntology instance; may be None if unnecessary
    :return string; answer to be output for this truple
    """
    answer = ''
    n_vars = len(triple.labels)
    if n_vars == 1:
        full_label = printResourceInfo(triple[0], triple, formal_query, formatter, o)
        answer = "%s\n" % full_label
    elif n_vars == 2:
        label_1 = formatter.printLabelsOfUri(triple[0])
        label_2 = formatter.printLabelsOfUri(triple[1])
        answer = "%s %s\n" % (label_1, label_2)
    elif n_vars == 3:
        s, p, o, p_type = rearrangeResult(triple, formal_query)
        s_label = formatter.printLabelsOfUri(s)
        p_label = formatter.printLabelsOfUri(p, p_type)
        o_label = formatter.printLabelsOfUri(o)
        answer = "%s %s %s\n" % (s_label, p_label, o_label)
    return answer


def rearrangeResult(triple, formal_query):
    """
    Rearrange the given result triple according to its member types to be output to the user
    :param triple: ResultRow instance
    :param formal_query: FormalQuery instance
    :return: (string, string, string), string triple with rearranged subject, property, and object; and type of the
    property in the triple (None if unknown)
    """
    p_type = None
    s, p, o = triple[0], triple[1], triple[2]
    property_second = False
    for v in triple.labels:
        if triple.labels[v] == 1:  # Variable at property position
            sc = formal_query.getSemanticConcept(v)
            if sc and isinstance(sc[0], SemanticConcept):
                if isinstance(sc[0].OE, (OntologyDatatypePropertyElement, OntologyObjectPropertyElement)):
                    property_second = True
                    p_type = 'objectProperty' if type(sc[0].OE) is OntologyObjectPropertyElement else 'datatypeProperty'
                    if sc[0].OE.reversed:
                        s, o = o, s
    if not property_second:
        raise SyntaxError("Property misplaced in result: (%s, %s, %s)" % (s, p, o))
    return s, p, o, p_type


def printResourceInfo(uri, triple, formal_query, formatter, o, label=None):
    """
    Print all known information about a given resource in the ontology
    :param uri: string or URIRef instance; the URI to consider
    :param triple: RowResult instance
    :param formal_query: FormalQuery instance
    :param formatter: OutputFormatter instance
    :param o: UpperOntology instance
    :param label: string; traditional label for the resource without added info
    :return: string
    """
    if label:
        full_label = label
    else:
        full_label = ''
    if isinstance(uri, basestring):
        from rdflib import URIRef
        uri = URIRef(uri)
    v = varOfURI(uri, triple)
    if v:
        sc = formal_query.getSemanticConcept(v)
        if sc and isinstance(sc[0], SemanticConcept):
            oe = sc[0].OE
            if isinstance(oe, OntologyInstanceElement):
                full_label = formatter.fullLabelForInstance(uri, oe)
    return full_label

def varOfURI(uri, triple):
    """
    Returns the associated variable for the given URI in a SPARQL result row
    :param uri: string or URIRef: an URI
    :param triple: ResultRow instance
    :return: string; variable name e.g. 'dp0', 'i1', or 'firstJoker'. None if not found.
    """
    var = None
    for v in triple.labels:
        if triple[v] == uri:
            var = v
            break
    return var


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


def objectIsInstance(sc):
    """
    Returns whether the given object is a Instance OE or SemanticConcept
    :param sc: Object instance
    :return: True if sc is a SemanticConcept instance with sc.OE a OntologyInstanceElement instance or a
    OntologyInstanceElement instance; False otherwise
    """
    return (isinstance(sc, SemanticConcept) and isinstance(sc.OE, OntologyInstanceElement)) \
        or isinstance(sc, OntologyInstanceElement)


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


def getAnswerType(scs):
    """
    Given a consolidated query, return those SemanticConcept instances that have been marked as the AT
    :param scs: List<List<SemanticConcept>>: a query's resolved Semantic Concepts
    :return: List<SemanticConcept>: OCs identified as the Answer Type of this question
    """
    at = []
    if scs:
        for sc_list in scs:
            if sc_list and sc_list[0].OE.main_subject:
                at = sc_list
                break
    return at


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
