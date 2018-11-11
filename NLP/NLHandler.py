import nltk
from NLP.constants import *
from util.TreeUtil import mutableCopy, treeRawString
from nltk.corpus import wordnet as wn


class NLHandler(object):
    """
    Natural Language Handler
    """
    def __init__(self, mapper):
        self.mapper = mapper

    def parseQuery(self, user_query):
        """
        Parses a user query and initializes a Query instance
        :param user_query: String
        :return: a Question instance
        """
        q = self.mapper.processQuestion(user_query)
        lemma = nltk.wordnet.WordNetLemmatizer()
        for ann in q.annotations:
            if ann.stem:
                p_lem = self.lemmatizeTree(mutableCopy(ann.tree), lemma)
                ann.lemma_tree = p_lem
        return q

    def lemmatizeTree(self, ptree, lemma):
        """
        Lemmatizes the tokens of a parse tree
        :param ptree: nltk.Tree instance
        :param lemma: an instantiated lemmatizer
        :return:
        """
        labels = [NN_TREE_POS_TAG, NNS_TREE_POS_TAG, NNP_TREE_POS_TAG, NNPS_TREE_POS_TAG]
        if type(ptree) is nltk.Tree:
            for child in ptree:
                if type(child) is nltk.Tree:
                    if child.height() == 2: # Pre-terminal
                        if child.label() in labels:
                            child[0] = self._lemmatizeWord(child[0], lemma)
                        else:
                            self.lemmatizeTree(child, lemma)
                elif ptree.label() in labels:
                    ptree[0] = self._lemmatizeWord(child, lemma)
        return ptree

    def _lemmatizeWord(self, word, lemma):
        """
        Lemmatizes a single word
        :param ptree: a string
        :param lemma: an instantiated lemmatizer
        :return: lemmatized sting
        """
        l = ''
        if word:
            if word.lower() in HARD_LEMMA:
                l = HARD_LEMMA[word.lower()]
            else:
                l = lemma.lemmatize(word)
        return l


def synonymsOfTree(self, ptree):
    """
    Returns synonyms for the whole string represented by the given parse tree
    :param ptree: an nltk.Tree instance
    :return: list<string> with synonyms
    """
    syns = set()
    if isinstance(ptree, nltk.Tree) and ptree.height() > 1:
        label = ptree.label()
        text = treeRawString(ptree)
        if text:
            text_norm = text.replace(" ", "_").lower()  # Compound names are underscored in Wordnet
            if label in POS_TAG_NOUN:
                pos_tag = wn.NOUN
            elif label in POS_TAG_ADVB:
                pos_tag = wn.ADV
            elif label in POS_TAG_JJ:
                pos_tag = wn.ADJ
            elif label in POS_TAG_VERB:
                pos_tag = wn.VERB
            else:
                return list()
            syn_set = wn.synsets(text_norm, pos=pos_tag)
            if len(syn_set) > 0:
                s = syn_set[0]  # Take into consideration only the most relevant synonym set
                lemmas = s.lemma_names()
                syns.update([l.replace("_", " ") for l in lemmas if l != text_norm])
    return list(syns)