from NLP.model.OE import *
from NLP.model.Joker import *
from NLP.model.SemanticConcept import *
from Ontovis.triple_utils import *

class FormalQuery(object):
    def __init__(self):
        """
        Formal (SPARQL, RDFLib) query constructor
        """
        self.semanticConcepts = []  # List<List<mixed(OntologyElement, Joker)>>
        self.sparql = ""  # Formal SPARQL query

    def from_concepts(self, concepts):
        """
        Populate this instance's attributes from the given SemanticConcepts with prepared Joker elements
        :param concepts: List<List<mixed(SemanticConcept, Joker)>> Prepared concepts from a consolidated user query
        :return:
        """
        from rdflib import RDF, XSD
        prefix_query = "prefix rdf: %s\nprefix xsd: %s\n" % (str(RDF), str(XSD))
        select_query = "SELECT DISTINCT"
        where_query = "WHERE { "
        order_query = " ORDER BY "
        select_set = ""
        concepts_len = len(concepts)
        for i, sc_list in enumerate(concepts):
            select_query += " "
            sample = sc_list[0]
            n_elements = len(sc_list)
            prev_sample = sc_list[i - 1][0] if i > 0 else None
            next_sample = sc_list[i + 1][0] if i < concepts_len - 1 else None
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
                        # TODO continue

