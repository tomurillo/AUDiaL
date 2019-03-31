import nltk
from util.TreeUtil import mutableCopy, treeRawString
from nltk.corpus import wordnet as wn
from NLP.model.Query import Query
from NLP.poc.filterCreator import *


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

    def getCardinalFilters(self, query):
        """
        Find cardinal (comparative, superlative) filters within a query's annotations
        :param query: Query instance with annotations
        :return: Query instance with cardinal filters
        """
        if isinstance(query, Query) and query.pocs:
            filter_creator = FilterCreator(query)
            query.filters = filter_creator.generateFilters()
        return query

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


def synonymsOfTree(ptree):
    """
    Returns synonyms for the whole string represented by the given parse tree
    :param ptree: an nltk.Tree instance
    :return: list<string> with synonyms
    """
    syns = []
    if isinstance(ptree, nltk.Tree) and ptree.height() > 1:
        label = ptree.label()
        text = treeRawString(ptree)
        if text:
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
            syns = synonymsOfWord(text, pos_tag)
    return syns


def synonymsOfWord(word, pos_tag=None, n_synonyms=None):
    """
    Returns synonyms from the Wordnet corpus for the given word
    :param word: string; word whose synonyms to fetch
    :param pos_tag: string; Wordnet part-of-speech tag of the input word, None (default) for all
    :param n_synonyms: int; maximum number of synonyms to return, None (default) for all
    :return: list<string> with synonyms of :word
    """
    syns = set()
    if word:
        text_norm = word.replace(" ", "_").lower()  # Compound names are underscored in Wordnet
        syn_set = wn.synsets(text_norm, pos=pos_tag)
        if len(syn_set) > 0:
            s = syn_set[0]  # Take into consideration only most relevant synonym set
            lemmas = s.lemma_names()
            syns.update([l.replace("_", " ") for l in lemmas if l != text_norm])
    return list(syns)[0:n_synonyms]


def similarityBetweenWords(word_one, word_two, metric):
    """
    Returns the numeric similarity between two given words
    :param word_one: string; a word
    :param word_two: string; a word
    :param metric: a function returning the similarity distance
    :return: float; similarity between word_one and word_two
    """
    similarity = 0.0
    if word_one and word_two:
        similarity = float(metric(word_one, word_two))
    return similarity


def soundexSimilarityBetweenWords(word_one, word_two):
    """
    Returns the soundex phonetic similarity between two given words
    :param word_one: string; a word
    :param word_two: string; a word
    :return: float; soundex similarity between word_one and word_two
    """
    similarity = 0.0
    if word_one and word_two:
        from textdistance import jaro  # Jaro-Winkler distance
        soundex_one = soundex(word_one)
        soundex_two = soundex(word_two)
        similarity = float(jaro(soundex_one, soundex_two))
        if similarity <= 0.5:  # Minimum soundex similarity is 0.5 because of padding zeroes
            similarity = 0.0
    return similarity


def soundex(word):
    """
    Returns the soundex representation of the given word
    :param word: string; a word
    :return: float; soundex code for the input word
    """
    soundex = ""
    if word:
        word = word.upper()
        soundex += word[0]
        dictionary = {"BFPV": "1", "CGJKQSXZ":"2", "DT":"3", "L":"4", "MN":"5", "R":"6", "AEIOUHWY":"."}
        for char in word[1:]:
            for key in dictionary.keys():
                if char in key:
                    code = dictionary[key]
                    if code != soundex[-1]:
                        soundex += code
        soundex = soundex.replace(".", "")
        soundex = soundex[:4].ljust(4, "0")
    return soundex
