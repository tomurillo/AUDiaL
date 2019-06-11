from nltk.tag.stanford import StanfordPOSTagger
from nltk.parse.stanford import StanfordParser
from nltk.parse import CoreNLPParser
from nltk.internals import find_jars_within_path
from nltk import Tree
import os
from NLP.model.Query import *
from NLP.poc.POCCreator import *


class GraphNavStanfordParser(object):
    def __init__(self, NLquery=None, parser='stanford', posTagger='stanford'):
        """
        Instantiate a POS tagger and NL parser.
        :param NLquery: string; input NL query (optional)
        :param parser: parser to be loaded. Either 'stanford' (local library) or 'stanford_web' (web service)
        :param posTagger: POS-tagger to be loaded. Either 'stanford' (local library) or 'stanford_web' (web service)
        """
        self.rawQuery = ""  # Unprocessed query
        self.normalizedFullQuery = ""  # Normalized query
        self.PT = None  # POS Tagger
        self.parser = None  # Grammar parser
        if NLquery:
            self.rawQuery = NLquery
            self.normalizedFullQuery = self.__normalizeQuery(NLquery)
        else:
            self.rawQuery = None
            self.normalizedFullQuery = None
        try:
            if posTagger == 'stanford':
                self.PT = self._loadStanfordPOSTagger()
            elif posTagger == 'stanford_web':
                self.PT = CoreNLPParser(url=self.__serviceEndpointWithAuth(), tagtype='pos')
            # No else; PT will default to nltk's default pos-tagger

            if parser == 'stanford':
                self.parser = self._loadStanfordParser()
            elif parser == 'stanford_web':
                self.parser = CoreNLPParser(url=self.__serviceEndpointWithAuth())
            else:
                raise ValueError('GraphNavStanfordParser: unknown parser %s' % parser)
        except ImportError as e:
            if str(e).startswith('cannot import name STANFORD'):
                raise ImportError(
                    ('No config file for web parser found in /NLP/parser. ' 
                     'Please edit and rename config-default.py to config.py'))

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
        query.pt = self.parseTree(clean_query)
        poc_creator = POCCreator(query)
        poc_creator.generatePOCs()
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
                      NX_TREE_POS_TAG, WHNP_TREE_POS_TAG]
        # First element in query matching heuristics
        for poc in query.pocs:
            if poc.tree.label() in focus_tags and poc not in ignore_list:
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
            focus_norm = focus.rawText.lower()
            if any(focus_norm.startswith(s) for s in start_tokens):
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
        Loads the local Stanford POS Tagger (warning: deprecated)
        @return StanfordPOSTagger instance
        """
        POS_JAR = "stanford-postagger-3.9.1.jar"
        POS_MODEL = "english-bidirectional-distsim.tagger"
        base = os.path.dirname(__file__)
        jarfile = os.path.normpath(os.path.join(base, "../lib", "postaggers", "stanford-postagger", POS_JAR))
        modelfile = os.path.normpath(os.path.join(base, "../lib", "postaggers", "stanford-postagger", "models",
                                                  POS_MODEL))
        tagger = StanfordPOSTagger(model_filename=modelfile, path_to_jar=jarfile)
        return tagger

    def _loadStanfordParser(self):
        """
        Loads the local Stanford Parser (warning: deprecated)
        @return An instance of the given parser class
        """
        PARSER_MODEL = "englishPCFG.ser.gz"
        base = os.path.dirname(__file__)
        stanfdir = os.path.normpath(os.path.join(base, "../lib", "parsers", "stanford-parser-full"))
        modelfile = os.path.normpath(os.path.join(stanfdir, "models", PARSER_MODEL))
        os.environ['STANFORD_PARSER'] = stanfdir
        os.environ['STANFORD_MODELS'] = stanfdir
        parser = StanfordParser(model_path=modelfile)
        parser._classpath = tuple(find_jars_within_path(stanfdir))
        return parser

    def __serviceEndpointWithAuth(self):
        """
        Add access credentials to the NLP service URL and return it
        :return: string; Stanford NLP service endpoint URL with added user/password information
        """
        from config import STANFORD_WEB_ENDPOINT, STANFORD_WEB_USER, STANFORD_WEB_PWD, STANFORD_WEB_PROTOCOL
        if STANFORD_WEB_USER and STANFORD_WEB_PWD:
            url = STANFORD_WEB_PROTOCOL + "://" + STANFORD_WEB_USER + ":" + STANFORD_WEB_PWD + "@" + \
                  STANFORD_WEB_ENDPOINT
        else:
            url = STANFORD_WEB_PROTOCOL + "://" + STANFORD_WEB_ENDPOINT
        if not url.endswith('/'):
            url += '/'
        return url
