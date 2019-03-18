from NLP.model.Joker import Joker
from NLP.model.SemanticConcept import *


class FormalQuery(object):
    def __init__(self, namespaces=None):
        """
        Formal (SPARQL, RDFLib) query constructor
        :param namespaces: List<tuple<string; string>> with namespaces prefixes and URIs to consider
        """
        self.semanticConcepts = []  # List<List<mixed(SemanticConcept, Joker)>>
        if namespaces is None:
            self.namespaces = []
        else:
            self.namespaces = namespaces
        self.sparql = ""  # Formal SPARQL query

    def getSemanticConcept(self, sc_id):
        """
        Get the Semantic Concept of the query with the given id
        :param sc_id: string; ID of a semantic concept
        :return: List<mixed(SemanticConcept; Joker)>: found overlapped SCs with the given id; empty list if none found
        """
        sc = []
        if sc_id and self.semanticConcepts:
            for sc_list in self.semanticConcepts:
                if sc_list and sc_list[0].id == sc_id:
                    sc = sc_list
                    break
        return sc

    def from_concepts(self, concepts):
        """
        Populate this instance's attributes from the given SemanticConcepts with prepared Joker elements
        :param concepts: List<List<mixed(SemanticConcept, Joker)>> Prepared concepts from a consolidated user query
        :return:
        """
        from oc.triple_utils import scIsProperty, objectIsLiteral, isPropertyReversed
        prefix_query = "\n".join(["prefix %s: <%s>" % (ns_prefix, ns_uri) for ns_prefix, ns_uri in self.namespaces])
        select_query = "SELECT DISTINCT"
        where_query = "WHERE { "
        order_query = " ORDER BY "
        select_set = ""
        concepts_len = len(concepts)
        for i, sc_list in enumerate(concepts):
            select_query += " "
            sample = sc_list[0]
            n_elements = len(sc_list)
            prev_sample = concepts[i - 1][0] if i > 0 else None
            next_sample = concepts[i + 1][0] if i < concepts_len - 1 else None
            if isinstance(sample, Joker):
                select_query += " ?%s" % sample.id
                if 'property' in sample.suitable_types and prev_sample and next_sample:
                    where_query += " { { ?%s ?%s ?%s } UNION " % (next_sample.id, sample.id, prev_sample.id)
                    where_query += " { ?%s ?%s ?%s } } " % (prev_sample.id, sample.id, next_sample.id)
            elif isinstance(sample, SemanticConcept):
                if isinstance(sample.OE, OntologyEntityElement):
                    select_query += " ?%s" % sample.id
                    where_query += "{ {"
                    for j, sc in enumerate(sc_list, 1):
                        where_query += " ?%s ?typeRelation%s <%s> . " % (sample.id, sample.id, sc.OE.uri)
                        if j < n_elements:
                            where_query += " } UNION { "
                        else:
                            where_query += " } }"
                elif isinstance(sample.OE, OntologyLiteralElement):
                    select_query += " ?%s" % sample.id
                    p_uri = sample.OE.triples[0][1]  # Literal OEs are grouped by property URI
                    # Filter for exact (case-insensitive) value of this literal
                    where_query += " FILTER REGEX(str(?%s), \"^%s$\", \"i\") . " % (sample.id, sample.OE.uri)
                    # Ensure that the previous property matches this Literal's property
                    if isinstance(prev_sample, SemanticConcept):
                        where_query += " FILTER ( ?%s=<%s>) " % (prev_sample.id, p_uri)
                elif scIsProperty(sample):
                    select_query += " ?%s" % sample.id
                    if isinstance(sample.OE, OntologyDatatypePropertyElement):
                        select_set += createSelectSetForDatatypeProperty(sample, prev_sample, next_sample)
                        where_query += createWhereSectionForDatatypeProperty(sc_list, prev_sample, next_sample)
                        order_query += createOrderSectionForDatatypeProperty(sample, prev_sample, next_sample)
                    elif prev_sample and next_sample:
                        sample.OE.reversed = isPropertyReversed(sample, prev_sample, next_sample)
                        if sample.OE.reversed or objectIsLiteral(prev_sample):
                            prev_sample, next_sample = next_sample, prev_sample
                        where_query += createWhereUnionSectionForProperty(sc_list, prev_sample, next_sample)
                    else:
                        from warnings import warn
                        warn('Property (%s) with no neighbor Semantic Concepts found:' % sample.id)
                elif isinstance(sample.OE, OntologyInstanceElement):
                    select_query += " ?%s" % sample.id
                    all_uris = []
                    for instance in sc_list:
                        all_uris.extend(instance.OE.uris)
                    from rdflib import RDF
                    if sample.OE.classUri:
                        where_query += " ?%s <%s> <%s> . " % (sample.id, RDF.type, sample.OE.classUri)
                    else:
                        where_query += " ?%s <%s> ?instType ." % (sample.id, RDF.type)
                    where_query += " FILTER ("
                    uris = list(set(all_uris))
                    n_uris = len(uris)
                    for j, uri in enumerate(uris, 1):
                        where_query += "?%s=<%s>" % (sample.id, uri)
                        if j < n_uris:
                            where_query += " || "
                    where_query += ") ."
        sparql = ""
        if select_set:
            sparql += "%s\n" % prefix_query
            sparql += select_set
        elif where_query != "WHERE { " and select_query != "SELECT DISTINCT":
            sparql += "%s\n" % prefix_query
            sparql += select_query
        if sparql:
            sparql += "\n%s }" % where_query
            if order_query != " ORDER BY ":
                sparql += order_query
            sparql += " LIMIT 100"
            self.sparql = sparql
            self.semanticConcepts = concepts


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
                prop.OE.reversed = True
            elif isinstance(prev_sc, Joker) and not isinstance(next_sc.OE, OntologyLiteralElement):
                subj = next_sc
                obj = prev_sc
                prop.OE.reversed = True
            else:
                subj = prev_sc
                obj = next_sc
        else:
            subj = prev_sc
            obj = next_sc
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
    from oc.triple_utils import scIsDatatypeProperty
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


def xsdDatatypeForSparqlQuery(lit_type_uri):
    """
    Converts a XSD datatype URI to an equivalent type string to be included in a SPARQL query
    :param lit_type_uri: string; XSD datatype URI
    :return: string; type URI in SPARQL form
    """
    from rdflib import XSD
    from oc.triple_utils import getNamespace, stripNamespace
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
    from oc.triple_utils import scIsProperty
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
