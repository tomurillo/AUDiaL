from oc.triple_utils import *


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

    def from_concepts(self, concepts):
        """
        Populate this instance's attributes from the given SemanticConcepts with prepared Joker elements
        :param concepts: List<List<mixed(SemanticConcept, Joker)>> Prepared concepts from a consolidated user query
        :return:
        """
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
                        if objectIsLiteral(prev_sample):
                            sample.OE.reversed = True
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
