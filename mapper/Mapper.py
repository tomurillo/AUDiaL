from NLP.parser.StanfordParser import *
from constants import *
from NLP.util.TreeUtil import treeRawString
from oc.OCUtil import *
from NLP.NLHandler import synonymsOfTree


class Mapper(object):
    """
    Prepares a user's query tokens to be mapped to OCs
    """
    def __init__(self):
        """
        Mapper class constructor
        """
        self.parser = GraphNavStanfordParser()
        self._toIgnore = []  # Children to be ignored when the father is ignored

    def processQuestion(self, text):
        """
        Instantiates a Query object given a user's question
        :param text: A user's raw string query
        :return: a Query instance
        """
        question = Query(text)
        if self.parser:
            question = self.parser.parseQuery(text)
            question.questionType = self.parser.findQuestionType(question)
            question.annotations = self.tokensToAnnotations(question)
        return question

    def ontologyBasedLookUp(self, o, q):
        """
        Looks up the annotations of the given query in the ontology and fills in their missing attributes
        :param o: UpperOntology (or subclass) instance
        :param o: NLHandler instance
        :param q: a Query instance
        :return: Updated query instance with list of annotations with associated OCs
        """
        clean_anns = removeSimilarAnnotations(q.annotations)
        for ann in clean_anns:
            text, types_found = self.annotationLookUp(o, ann)
            if types_found:
                ann.inOntology = True
                ann.oc_type = types_found
                ann.text = text
            else:
                syns, types_found = self.annotationSynonymsLookUp(o, ann)
                if types_found:
                    ann.inOntology = True
                    ann.oc_type = types_found
                    ann.text = syns[0]  # Ignore other synonyms for now
            self.updateAnnotationExtras(ann, o)
        q.annotations = clean_anns
        return q

    def annotationLookUp(self, o, annotation, text_type='all'):
        """
        Search an annotation's text in the ontology.
        :param o: UpperOntology (or subclass) instance
        :param annotation: An NLP.Annotation instance
        :param text_type: What to search for: 'individual', 'class', 'property', 'value', or 'all' (default)
        :return: tuple (found text, types of OC found); or False if none were found
        """
        text = None
        types = False
        if annotation and o:
            if annotation.stem:  # Look up lemmatized words first
                text = treeRawString(annotation.lemma_tree)
                types = self.textLookUp(o, text, text_type)
            if not types:
                text = annotation.rawText
                types = self.textLookUp(o, text, text_type)
        return text, types

    def annotationSynonymsLookUp(self, o, annotation, text_type='all'):
        """
        Search for synonyms of an annotation's text in the ontology.
        :param o: UpperOntology (or subclass) instance
        :param annotation: An NLP.Annotation instance
        :param text_type: What to search for: 'individual', 'class', 'property', 'value', or 'all' (default)
        :return: tuple (list, list): the found texts, types of OC found; or False if none were found
        """
        text = set()
        types = set()
        if annotation and o:
            if annotation.stem:  # Look up lemmatized words first
                syn = synonymsOfTree(annotation.lemma_tree)
                for s in syn:
                    t = self.textLookUp(o, s, text_type)
                    if t:
                        text.update(s)
                        types.update(t)
            if not types:  # Lemmatization not required or nothing found so far
                syn = synonymsOfTree(annotation.tree)
                for s in syn:
                    t = self.textLookUp(o, s, text_type)
                    if t:
                        text.update(s)
                        types.update(t)
        return list(text), list(types)

    def textLookUp(self, o, text, text_type='all'):
        """
        Search a string in the ontology
        :param o: UpperOntology (or subclass) instance
        :param text: A free-formed string
        :param text_type: What to search for: 'individual', 'class', 'property', 'value', or 'all' (default)
        :return: The type(s) if something of the given type exists in o; False otherwise
        """
        types = False
        if text and o:
            types = o.thingExists(text, text_type)
            if not types:
                types = False
        return types

    def tokensToAnnotations(self, query, preferLonger=False):
        """
        Converts tokens (subtrees) of a user query to annotations to be searched in the ontology
        :param query: Query instance (must have instantiated POCs and pt attributes)
        :param preferLonger: boolean; whether to remove overlapping annotations
        :return: a list of Annotation instances
        """
        annotations = []
        if query.tokens and query.pt:
            tokens = query.pt.leaves()
            subtrees = query.pt.subtrees()  # Fetch all subtrees (sub-phrases and words of query)
            visited = []
            for t in subtrees:
                words = t.leaves()
                n_words = len(words)
                pos = positionsInList(tokens, words)
                if pos:
                    start, end = pos[visited.count(words)]
                else:
                    start, end = -1, -1
                if len(t) > 1 or type(t[0]) is not nltk.Tree:  # Ignore when same words will come again
                    visited.append(words)
                if n_words == 1:
                    ignore = self._isTokenIgnored(t)
                else:
                    ignore = self._isPhraseIgnored(t)
                    if not ignore and n_words == 2:
                        ignore = self._isWordPairIgnored(t)
                if not ignore:
                    annotation = Annotation()
                    annotation.rawText = quick_norm(treeRawString(t))
                    annotation.tree = immutableCopy(t)
                    annotation.start = start
                    annotation.end = end
                    # If token is plural it needs to be sent to stemmer
                    stem_first = False
                    if n_words == 1 and self._tokenIsPlural(t):
                        stem_first = True
                    elif self._phraseRequiresSpecialTreatment(t):
                        stem_first = True
                        if t.height() >= 3:
                            _, _, prepres, _ = getPrePreTerminals(t)
                            tree_clean = t.copy(deep=True)
                            for prepreterminal in prepres:
                                remove = True
                                for preterminal in prepreterminal:
                                    if NN_TREE_POS_TAG in preterminal.label():
                                        remove = False
                                    elif JJ_TREE_POS_TAG in preterminal.label() and "WH" not in prepreterminal.label():
                                        remove = False
                                if remove:
                                    tree_copy = tree_clean.copy(deep=True)
                                    tree_clean = removeSubTree(tree_copy, prepreterminal)
                            annotation.tree = immutableCopy(tree_clean)
                            annotation.rawText = quick_norm(treeRawString(tree_clean))
                    annotation.stem = stem_first
                    annotations.append(annotation)
        if preferLonger:
            return removeOverlappingAnnotations(annotations)
        else:
            return annotations

    def updateAnnotationExtras(self, ann, o):
        """
        Update the extra features of an annotation according to its ontological type
        :param ann: A previously looked-up annotation
        :param o: Ontology instance
        """
        if ann.inOntology:
            p_name = None
            if o_c.OTYPE_CLASS in ann.oc_type:
                distance = o.specificityOfElement(o.stripNamespace(ann.oc_type[o_c.OTYPE_CLASS]))
                ann.extra['class_specScore'] = distance
            if o_c.OTYPE_IND in ann.oc_type:
                #  Add class URIs of instance to Annotation
                ind_uri = o.stripNamespace(ann.oc_type[o_c.OTYPE_IND])
                class_uris = o.getClassOfElement(ind_uri, stripns=False)
                if class_uris:
                    ann.extra['classUri'] = class_uris
                    if len(class_uris) > 1:
                        max_spec = -1
                        dir_class_uri = ''
                        for c_uri in class_uris:
                            spec = o.specificityOfElement(c_uri)
                            if spec > max_spec:
                                max_spec = spec
                                dir_class_uri = c_uri
                        ann.extra['directClassUri'] = dir_class_uri
                    else:
                        ann.extra['directClassUri'] = class_uris[0]
            if o_c.OTYPE_DTPROP in ann.oc_type:
                p_name = o.stripNamespace(ann.oc_type[o_c.OTYPE_DTPROP])
            if o_c.OTYPE_OPROP in ann.oc_type:
                if p_name:
                    from warnings import warn
                    warn('Dtype and object properties with same name found (%s). Priority given to object property.'
                         % p_name)
                p_name = o.stripNamespace(ann.oc_type[o_c.OTYPE_OPROP])
            if p_name:
                #  Add property's range and domain to Annotation
                dom = o.domainOfProperty(p_name, stripns=False)
                if dom:
                    ann.extra['domain'] = dom
                ran = o.rangeOfProperty(p_name, stripns=False)
                if ran:
                    ann.extra['range'] = ran
                specificity = o.specificityOfElement(o.stripNamespace(p_name))
                ann.extra['prop_specScore'] = specificity
                distance = o.distanceScoreOfProperty(o.stripNamespace(p_name))
                ann.extra['prop_distScore'] = distance
            if o_c.OTYPE_LITERAL in ann.oc_type:
                literal_uri = ann.oc_type[o_c.OTYPE_LITERAL]
                #  Add Literal's context (triples where it appears)
                triples = o.contextOfLiteral(literal_uri)
                ann.extra['triples'] = triples

    def _isTokenIgnored(self, ptree):
        """
        Returns whether the given token (a single word) needs to be ignored in OC mapping
        :param ptree: a preterminal nltk.Tree
        :return: True if the token must be ignored, False otherwise
        """
        ignore = False
        if isinstance(ptree, nltk.Tree):
            if ptree in self._toIgnore:
                ignore = True
            else:
                label = ptree.label()
                if label in TOKEN_IGNORE_LABELS:
                    ignore = True
                else:
                    child = ptree[0]
                    if isinstance(child, basestring):
                        child_norm = quick_norm(child)
                        if label in TOKEN_IGNORE_VERB_LABELS:
                            if child_norm in TOKEN_IGNORE_VERBS:
                                ignore = True
                        elif child_norm in TOKEN_IGNORE_SP_ARTICLE:
                            ignore = True
                    elif isinstance(child, nltk.Tree):
                        ignore = self._isTokenIgnored(child)  # Keep digging until the word label is found
        return ignore

    def _isWordPairIgnored(self, ptree):
        """
        Returns whether the given token pair needs to be ignored in OC mapping.
        Considers phrases such as 'show me' and 'give me'
        :param ptree: nltk.Tree
        :return: True if the tokens must be ignored, False otherwise
        """
        from NLP.poc.const import TOKEN_IGNORE_PAIR
        ignore = False
        if isinstance(ptree, nltk.Tree):
            if ptree in self._toIgnore:
                ignore = True
            else:
                treestr = quick_norm(treeRawString(ptree))
                if treestr in TOKEN_IGNORE_PAIR:
                    ignore = True
        return ignore

    def _isPhraseIgnored(self, ptree):
        """
        Returns whether the given phrase needs to be ignored in OC mapping. Considers WH- phrases
        :param ptree: nltk.Tree
        :return: True if the tokens must be ignored, False otherwise
        """
        ignore = False
        if isinstance(ptree, nltk.Tree):
            if ptree in self._toIgnore:
                ignore = True
            else:
                label = ptree.label()
                if label in TOKEN_IGNORE_WH_PHRASE:
                    for child in ptree:
                        if isinstance(child, nltk.Tree):
                            child_label = child.label()
                            if child_label in TOKEN_IGNORE_WH_CHILD:
                                ignore = True
                elif label in TOKEN_IGNORE_PHRASE:
                    ignore = True
        return ignore

    def _tokenIsPlural(self, ptree):
        """
        Checks whether a word is a plural noun
        :param ptree: Pre(pre)terminal parse tree containing the word
        :return: True if word is (potentially) plural, False otherwise
        """
        plural = False
        if isinstance(ptree, nltk.Tree):
            plural_tags = [NN_TREE_POS_TAG, NNS_TREE_POS_TAG, NNPS_TREE_POS_TAG]  # NN because of mass nouns
            plural = ptree.label() in plural_tags
            if not plural:
                child = ptree[0]
                if isinstance(ptree, nltk.Tree):
                    plural = self._tokenIsPlural(child)
        return plural

    def _phraseRequiresSpecialTreatment(self, ptree):
        """
        Checks whether a sentence needs special treatment by the mapper (filtering certain words out)
        :param ptree: Pre(pre)terminal parse tree containing the word
        :return: True if the phrase requires special treatment; False otherwise
        """
        special = False
        if isinstance(ptree, nltk.Tree) and ptree.height() < 5:  # Pre-pre-preterminal or lower
            label = ptree.label()
            if NP_TREE_POS_TAG in label:  # Considers NP (singular and plural) and WHNP
                special = True
        return special
