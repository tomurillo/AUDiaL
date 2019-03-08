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
        :param concepts: List<List<mixed(OntologyElement, Joker)>> Prepared concepts from a consolidated user query
        :return:
        """
        #  TODO
