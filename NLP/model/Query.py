

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
        self.focus = None  # POC instance
        self.pocs = []
        self.tokens = []  # List<(string, string)>: list of (word, part-of-speech) tuples of each word in the query
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

    def to_dict(self):
        """
        Converts this Query instance to an equivalent dictionary (of built-in types) representation
        :return: dict
        """
        d = {'rawQuery': self.rawQuery, 'questionType': self.questionType, 'answerType': self.answerType}
        if self.focus:
            d['focus'] = self.focus.to_dict()
        else:
            d['focus'] = None
        d['annotations'] = [ann.to_dict() for ann in self.annotations]
        d['pocs'] = [p.to_dict() for p in self.pocs]
        d['tokens'] = [list(t) for t in self.tokens]
        d['pt'] = str(self.pt) if self.pt else None
        d['semanticConcepts'] = []
        for sc_list in self.semanticConcepts:
            d['semanticConcepts'].append([sc.to_dict() for sc in sc_list])
        return d

    def from_dict(self, d):
        """
        Populates this instances's attributes from the given dictionary
        :param d:
        :return: None; updates current instance
        """
        if type(d) is dict:
            from NLP.model.POC import POC
            from NLP.model.SemanticConcept import SemanticConcept
            from NLP.model.Annotation import Annotation
            self.rawQuery = d.get('rawQuery', '')
            self.questionType = d.get('questionType', QuestionType.VOID)
            self.answerType = d.get('answerType')
            focus_dict = d.get('focus')
            if focus_dict:
                focus = POC()
                focus.from_dict(focus_dict)
                self.focus = focus
            else:
                self.focus = None
            anns = d.get('annotations', [])
            self.annotations = []
            for a_dict in anns:
                a = Annotation()
                a.from_dict(a_dict)
                self.annotations.append(a)
            pocs = d.get('pocs', [])
            self.pocs = []
            for p in pocs:
                poc = POC()
                poc.from_dict(p)
                self.pocs.append(poc)
            tokens = d.get('tokens', [])
            self.tokens = [tuple(t) for t in tokens]
            pt = d.get('pt')
            if pt:
                from nltk import Tree
                self.pt = Tree.fromstring(pt)
            else:
                self.pt = None
            scs = d.get('semanticConcepts', [])
            self.semanticConcepts = []
            for sc_dict_list in scs:
                sc_list = []
                for sc_dict in sc_dict_list:
                    sc = SemanticConcept()
                    sc.from_dict(sc_dict)
                    sc_list.append(sc)
                self.semanticConcepts.append(sc_list)
        else:
            raise ValueError('Query.from_dict: parameter must be of type dict.')
