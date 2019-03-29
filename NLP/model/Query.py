from NLP.model.OE import *
from NLP.model.QueryFilter import *

class QuestionType(object):
    """
    Enum-workaround class: NL query types
    See Damljanovic, D. (2011)
    """
    VOID, BOOLEAN, COUNT, BOW, = range(4)


class Query(object):
    def __init__(self, rawQuery=''):
        """
        Query (NL question) constructor
        """
        self.rawQuery = rawQuery
        self.questionType = QuestionType.VOID
        self.focus = None  # POC instance
        self.pocs = []
        self.tokens = []  # List<(string, string)>: list of (word, part-of-speech) tuples of each word in the query
        self.pt = None  # Syntax parse tree (PT) of type nltk.Tree
        self.answerType = []  # List<OntologyElement>
        self.semanticConcepts = []  # list<list<SemanticConcept>>: overlapped-by-text SCs, first one overlaps the rest
        self.annotations = []  # Query substrings to be looked up in the ontology; they do *not* have to be in the KB
        self.filters = []  # Query filter instances

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
                    import warnings
                    warnings.warn('Warning: flattening list of ambiguous SemanticConcepts!')
        return flat_scs

    def ocs_consistent(self):
        """
        Check whether the OCs of the Query are consistent (all overlapping OCs are resources of the same class)
        :return: True is OCs are consistent; False otherwise
        """
        consistent = True
        for sc_list in self.semanticConcepts:
            if len(sc_list) > 1:
                first_type = type(sc_list[0].OE)
                if not all(isinstance(sc.OE, first_type) for sc in sc_list):
                    consistent = False
                    break
        return consistent

    def to_dict(self):
        """
        Converts this Query instance to an equivalent dictionary (of built-in types) representation
        :return: dict
        """
        d = {'rawQuery': self.rawQuery, 'questionType': self.questionType}
        if self.focus:
            d['focus'] = self.focus.to_dict()
        else:
            d['focus'] = None
        d['answerType'] = [at.to_dict() for at in self.answerType]
        d['annotations'] = [ann.to_dict() for ann in self.annotations]
        d['pocs'] = [p.to_dict() for p in self.pocs]
        d['tokens'] = [list(t) for t in self.tokens]
        d['pt'] = str(self.pt) if self.pt else None
        d['semanticConcepts'] = []
        d['filters'] = [f.to_dict for f in self.filters]
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
            answerType = d.get('answerType', [])
            self.answerType = []
            for at_dict in answerType:
                if at_dict:
                    oe_type = at_dict.get('type', 'OntologyElement')
                    if oe_type in globals():
                        oe_class = globals()[oe_type]
                        oe_instance = oe_class()
                        oe_instance.from_dict(at_dict)
                        self.answerType.append(oe_instance)
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
            filters = d.get('filters', [])
            self.filters = []
            for f_dict in filters:
                if f_dict:
                    f_type = f_dict.get('type', 'QueryFilter')
                    if f_type in globals():
                        f_class = globals()[f_type]
                        f_instance = f_class()
                        f_instance.from_dict(f_type)
                        self.filters.append(f_instance)
        else:
            raise ValueError('Query.from_dict: parameter must be of type dict.')
