

class QuestionType(object):
    """
    Enum-workaround class: NL query types
    See Damljanovic, D. (2011)
    """
    VOID, BOOLEAN, COUNT, BOW, = range(4)


class Query(object):
    def __init__(self, rawQuery):
        """
        Query (NL question) constructor
        """
        self.rawQuery = rawQuery
        self.questionType = QuestionType.VOID
        self.focus = None
        self.pocs = []
        self.tokens = []
        self.pt = None  # Syntax parse tree (PT) of type nltk.Tree
        self.answerType = None
        self.semanticConcepts = []  # list<list<SemanticConcept>>: overlapped-by-text SCs, first one overlaps the rest
        self.annotations = []  # Annotations to be looked up in the ontology; they do *not* have to be in the KB

    def flattened_scs(self):
        """
        Flattens the list of overlapped SemanticConcept instances, returning the main overlapping ones and ignoring
        those nested below (i.e. overlapped)
        :return: list<SemanticConcept>
        """
        flat_scs = []
        for scs in self.semanticConcepts:
            if scs:
                flat_scs.append(scs[0])
                if len(scs) > 1:
                    import sys
                    print('Warning: flattening list of ambiguous SemanticConcepts!', sys.stderr)
        return flat_scs
