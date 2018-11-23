from NLP.util.TreeUtil import *
from NLP.constants import *
from NLP.model.POC import *


class Consolidator(object):
    """
    Class responsible for automatically mapping a query's POCs into OCs
    """
    def __init__(self):
        """
        Consolidator constructor
        """
        pass

    def consolidateQuery(self, query):
        """
        Perform an automatic mapping of POCs into OCs
        :param query: A Query instance
        :return:
        """
        newpocs = self.separatePOCswithJJ(query.pocs)


    def separatePOCswithJJ(self, pocs):
        """
        Given a list of POCs, split each POC containing an adjective into two new POCs; one containing the adjective
        and one containing everything else
        :param poc: A POC instance
        :return: (POC, POC) tuple
        """
        newpocs = []
        #  Node tags that indicate an adjective in a pre-terminal POC
        adj_tags = [JJ_TREE_POS_TAG, VBN_TREE_POS_TAG, VBG_TREE_POS_TAG, RBS_TREE_POS_TAG, ADJP_TREE_POS_TAG,
                    JJR_TREE_POS_TAG, JJS_TREE_POS_TAG]
        for poc in pocs:
            others = set()
            adjs = []
            poc_preters = getSubtreesAtHeight(poc.tree, 2)
            if len(poc_preters) > 1:
                for preter in poc_preters:
                    if preter.label() in adj_tags:
                        adjs.append(preter)
                    else:
                        others.add(preter)
            else:
                others.add(poc_preters[0])
            if others:
                newpoc = self.updateSplitPOC(poc, list(others), poc.tree.label())
                newpocs.append(newpoc)
            if adjs:
                adjpoc = self.updateSplitPOC(poc, adjs, poc.tree.label())
                newpocs.append(adjpoc)
        return newpocs

    @staticmethod
    def updateSplitPOC(poc, new_trees, root_label):
        """
        Returns an updated POC from a list of split parse trees
        :param poc: POC instance to update
        :param new_trees: list<nlkt.Tree>: pre-terminal trees that make up the new POC
        :param root_label: the label of the new POC Parse Tree root
        :return: a new POC instance
        """
        newPoc = None
        if poc and poc.start >= 0 and poc.end >= 0:
            if len(new_trees) > 1:
                newrawtext = ''
                new_tokens = []
                for t in new_trees:
                    newrawtext += ' ' + treeRawString(t)
                    new_tokens.extend(t.leaves())
                newtree = nltk.Tree(root_label, new_trees)
                newPoc = POC(newrawtext, newtree)
                newPoc.start, newPoc.end = Consolidator.getSplitPOCOffsets(poc, new_tokens)
                newPoc.head = poc.head
                newPoc.modifiers = poc.modifiers
            else:
                newPoc = poc
        return newPoc

    @staticmethod
    def getSplitPOCOffsets(poc, new_tokens):
        """
        Utility function to compute the start and end offsets of a split POC
        :param poc: Original POC instance
        :param new_tokens: List<string>: tokens of the split POC
        :return: (int, int) start and end offsets of the split POC
        """
        old_tokens = poc.tree.leaves()
        start_delay = 0
        end_delay = 0
        i = 0
        while i < len(old_tokens) and old_tokens[i] != new_tokens[-1]:
            start_delay += 1
            i += 1
        i = len(old_tokens) - 1
        while i >= 0 and old_tokens[i] != new_tokens[-1]:
            end_delay += 1
            i -= 1
        newstart = poc.start + start_delay
        newend = poc.end - end_delay
        return newstart, newend
