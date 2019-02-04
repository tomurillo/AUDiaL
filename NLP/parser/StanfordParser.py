import const as c
from nltk.tag.stanford import StanfordPOSTagger
from nltk.parse.stanford import StanfordParser
from nltk.internals import find_jars_within_path
from nltk import Tree
import os
from GeneralUtil import asWindows
from NLP.model.Query import *
from NLP.model.POC import *
from NLP.util.TreeUtil import *

class GraphNavStanfordParser(object):
    def __init__(self, NLquery = None, parser = 'stanford', posTagger = 'stanford'):
        self.rawQuery = "" # Unprocessed query
        self.normalizedFullQuery = "" # Normalized query
        self.PT = None # POS Tagger
        self.parser = None # Grammar parser
        if NLquery:
            """ Query as given by the user """
            self.rawQuery = NLquery
            """ User query after basic normalization """
            self.normalizedFullQuery = self.__normalizeQuery(NLquery)
        else:
            self.rawQuery = None
            self.normalizedFullQuery = None
        if posTagger == 'stanford':
            self.PT = self._loadStanfordPOSTagger()
        if parser == 'stanford':
            self.parser = self._loadStanfordParser()

    def posTree(self, q):
        """
        Returns a Part-of-Speech tree for the given query
        @param q: the NL query
        @return array: POS Tree for q
        """
        if not q:
            q = self.normalizedFullQuery
        tree = None
        if self.PT:
            tree = self.PT.tag(q.split())
        else:
            # Fall back to NLTK's default tagger
            from nltk import pos_tag
            tree = pos_tag(q.split())
        return tree

    def parseTree(self, q):
        """
        Returns a syntax parse tree for the given query
        @param q: the NL query
        @return array: Parse Tree of q
        """
        if not q:
            q = self.normalizedFullQuery
        tree = None
        if self.parser:
            tree = list(self.parser.raw_parse(q))[0]
        else:
            raise SystemError("No parser loaded in NLHandler.")
        return tree

    def isBOW(self, posTags):
        """
        Returns whether the given POS tree represents
        a bag-of-words (keyword list) query
        @param posTags: a full POS list representing a user query
        @return bool: True if tree is a BOW; False otherwise
        """
        nonBowTags = [IN_TREE_POS_TAG, EX_TREE_POS_TAG, JJR_TREE_POS_TAG, JJS_TREE_POS_TAG, MD_TREE_POS_TAG,
                      RBR_TREE_POS_TAG, RBS_TREE_POS_TAG, TO_TREE_POS_TAG, VBD_TREE_POS_TAG, VBG_TREE_POS_TAG,
                      VBN_TREE_POS_TAG, VBP_TREE_POS_TAG, VBZ_TREE_POS_TAG, WDT_TREE_POS_TAG, WP_TREE_POS_TAG,
                      WPDOLLAR_TREE_POS_TAG, WRB_TREE_POS_TAG]
        if not posTags:
            return False
        isbow = True
        for w, tag in posTags:
            if tag in nonBowTags:
                isbow = False
                break
        return isbow

    def parseQuery(self, user_query):
        """
        Parses a user query and initializes a Query instance
        :param user_query: String
        :return: a Question instance
        """
        if not user_query:
            return "Please enter a question"
        clean_query = self.__normalizeQuery(user_query)
        query = Query(clean_query)
        query.tokens = self.posTree(clean_query)
        tree = self.parseTree(clean_query)
        query_token_list = tree.leaves()
        p_pocs = getPocs(tree)  # Potential POCs
        pocs = []
        visited = []
        for poc_tree in p_pocs:
            # Compute head
            head = getHeadOfNounPhrase(poc_tree)
            # Compute modifiers
            modif = getModifiersOfNounPhrase(poc_tree)
            # Remove determinants (DT) from POC
            poc_tree_clean = removeSubElementFromTree(poc_tree, DT_TREE_POS_TAG)
            # Initialize POC
            poc = POC(treeRawString(poc_tree_clean), poc_tree_clean)
            poc.head = head
            poc.modifiers = modif
            # Compute start and end offsets of POC
            poc_token_list = poc_tree.leaves()
            pos = positionsInList(query_token_list, poc_token_list)
            if pos:
                start, end = pos[visited.count(poc_token_list)]
            else:
                start, end = -1, -1
            if len(poc_tree) > 1 or type(poc_tree[0]) is not nltk.Tree:
                visited.append(poc_token_list)
            if poc_tree == poc_tree_clean:
                poc.start = start
            else:  # DTs have been removed from POC
                n_words_before = len(poc_token_list)
                n_words_after = len(poc_tree_clean.leaves())
                poc.start = start + n_words_before - n_words_after
            poc.end = end
            poc.start_original = poc.start
            poc.end_original = poc.end
            pocs.append(poc)
        query.pt = tree
        query.pocs = pocs
        self.findFocus(query)
        return query

    def findFocus(self, query):
        """
        Returns a user query's focus (a POC) and stores
        it in the Query instance
        @param query: Query instance
        :return: POC instance
        """
        focus = None
        ignore_list = [] # POCs to ignore as they are almost certainly not the question focus
        ignore_list.append(Tree(NP_TREE_POS_TAG, [Tree(DT_TREE_POS_TAG, ['the']), Tree(NN_TREE_POS_TAG, ['number'])]))
        ignore_list.append(Tree(NP_TREE_POS_TAG, [Tree(DT_TREE_POS_TAG, ['the']), Tree(NN_TREE_POS_TAG, ['amount'])]))
        focus_tags = [NP_TREE_POS_TAG, NN_TREE_POS_TAG, NNP_TREE_POS_TAG, NNS_TREE_POS_TAG, NNPS_TREE_POS_TAG,
                      NX_TREE_POS_TAG]
        # First element in query matching heuristics
        for poc in query.pocs:
            if poc.tree.label() in focus_tags and not poc in ignore_list:
                poc.mainSubjectPriority = self.priorityOfFocus(poc)
                focus = poc.deepcopy()  # Focus has to be preserved after POC resolution
                query.focus = focus
                break
        return focus

    def priorityOfFocus(self, focus):
        """
        Returns the Main Subject priority of a question's focus
        :param focus: POC instance representing a Query's focus
        :return:
        """
        priority = POC.MSUB_PRIORITY_MIN
        if focus and focus.rawText:
            start_tokens = ["how", "where", "when", "since", "since", "who", "list", "show", "tell"]
            if any(focus.rawText.lower().startswith(s) for s in start_tokens):
                priority = POC.MSUB_PRIORITY_MAX
        return priority

    def findQuestionType(self, query):
        """
        Tries to infer the high-level question type of a Query instance (BOW, boolean, count, other)
        :param query: a initialized and parser Query
        :return:
        """
        qtype = QuestionType.VOID
        found = False
        postags = query.tokens
        if self.isBOW(postags):
            qtype = QuestionType.BOW
            found = True
        ptree = query.pt
        if not found and ptree:
            preters = getSubtreesAtHeight(ptree, 2)  # Pre-terminals
            first_preter = preters[0]
            if first_preter and type(first_preter) is Tree:
                label = first_preter.label()
                word = quick_norm(first_preter[0])
                if label.startswith(VB_TREE_POS_TAG):
                    non_bool_verbs = ["show", "give", "list", "count"]
                    if word not in non_bool_verbs:
                        found = True
                        qtype = QuestionType.BOOLEAN
                if not found:
                    if word.startswith("count"):
                        qtype = QuestionType.COUNT
                    elif word.startswith("how") and len(preters) > 1:
                        whadjp_adjs = ["many", "much"]  # Wh-adjective phrase adjectives
                        second_preter = preters[1]
                        second_word = quick_norm(second_preter[0])
                        if second_word in whadjp_adjs:
                            qtype = QuestionType.COUNT
        return qtype


    def __normalizeQuery(self, q):
        """
        Performs simple normalization on a given query
        @param q: the NL query
        @return string: the normalized query
        """
        nq = ""
        p = '.,;'
        to_remove = '?!'  # Question and exclamation marks confuse Stanford parser
        if q:
            nq = q.lower()
            for punct in p:
                nq = nq.replace(punct, " ")
            for rem in to_remove:
                nq = nq.replace(rem, "")
        return nq

    def _loadStanfordPOSTagger(self):
        """
        Loads the Stanford POS Tagger
        @return StanfordPOSTagger instance
        """
        base = os.path.realpath(__file__)[:-len("parser/StanfordParser.pyc")]
        if not base.endswith("/") or not base.endswith("\\"):
            base += "/"
        stanfdir = base + 'lib/postaggers/stanford-postagger/'
        modeldir = stanfdir + 'models/'
        if c.CURR_ENV == 'windows':
            stanfdir = asWindows(stanfdir)
            modeldir = asWindows(modeldir)
        jarfile = stanfdir + 'stanford-postagger-3.9.1.jar'
        modelfile = modeldir + 'english-bidirectional-distsim.tagger'
        tagger = StanfordPOSTagger(model_filename=modelfile, path_to_jar=jarfile)
        return tagger

    def _loadStanfordParser(self):
        """
        Loads a Stanford Parser
        @return An instance of the given parser class
        """
        base = os.path.realpath(__file__)[:-len("parser/StanfordParser.pyc")]
        if not base.endswith("/") or not base.endswith("\\"):
            base += "/"
        stanfdir = base + 'lib/parsers/stanford-parser-full/'
        modeldir = stanfdir + 'models/'
        if c.CURR_ENV == 'windows':
            stanfdir = asWindows(stanfdir)
            modeldir = asWindows(modeldir)
        #parfile = stanfdir + 'stanford-parser.jar'
        #mfile = stanfdir + 'stanford-parser-3.9.1-models.jar'
        modelfile = modeldir + 'englishPCFG.ser.gz'
        os.environ['STANFORD_PARSER'] = stanfdir
        os.environ['STANFORD_MODELS'] = stanfdir
        parser = StanfordParser(model_path=modelfile)
        parser._classpath = tuple(find_jars_within_path(stanfdir))
        return parser