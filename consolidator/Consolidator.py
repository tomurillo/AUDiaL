from NLP.util.TreeUtil import *
from NLP.constants import *
from NLP.model.POC import *
from consolidator.constants import *
from oc.OCUtil import SemanticConceptListCompareOffset

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
        :return: A consolidated Query with unresolved POCs and updated OCs
        """
        pocs_no_jj = self.separatePOCswithJJ(query.pocs)
        query.pocs = self.removeUselessTokens(pocs_no_jj)
        query = self.cleanSemanticConcepts(query)
        query = self.consolidatePOCsWithOCs(query)
        return query

    def consolidatePOCsWithOCs(self, q):
        """
        Given a question, remove those POCs which overlap with any of its OCs and update overlapped OCs with
        information from the POC.
        :param q: A Query instance
        :return: Updated Query instance
        """
        pocs_clean = []
        for poc in q.pocs:
            matching_ocs = self.matchingOCsOfPOC(poc, q.semanticConcepts)
            add = True  # Add POCs not contained in any OC for future resolution
            if matching_ocs:
                add = False
            else:
                for scs in q.semanticConcepts:
                    if not add:
                        break
                    for i, sc in enumerate(scs):
                        if sc.overlapsPOC(poc):
                            add = False
                            break
                        elif poc.overlapsOC(sc):
                            sc.OE.annotation.tree = poc.tree
                            if i == 0:
                                #  Create new POC without the contained OC
                                new_tree = removeSubTree(poc.tree, sc.OE.annotation.tree)
                                if new_tree and isinstance(new_tree, nltk.Tree):
                                    new_poc = POC()
                                    new_poc.tree = new_tree
                                    new_poc.start_original = poc.start_original
                                    new_poc.end_original = poc.end_original
                                    new_poc.start, new_poc.end = Consolidator.getSplitPOCOffsets(poc, new_tree.leaves())
                                    new_poc.rawText = treeRawString(new_tree)
                                    new_poc.head = poc.head
                                    new_poc.modifiers = poc.modifiers
                                    new_poc.mainSubjectPriority = poc.mainSubjectPriority
                                    pocs_clean.append(new_poc)
                                    add = False
            if add:
                pocs_clean.append(poc)
        q.pocs = pocs_clean
        return q

    def matchingOCsOfPOC(self, poc, semantic_concepts):
        """
        Returns which of the given Semantic Concepts match the given POC (i.e. they have the same start and
        end offsets)
        :param poc: a POC instance
        :param semantic_concepts: list<list<SemanticConcept>>: a Query's overlapping OCs
        :return: list<list<SemanticConcept>>: Overlapping OCs matching the given POC
        """
        match_found = False
        filtered_ocs = []
        for i, sc_list in enumerate(semantic_concepts):  # Overlapping OCs
            if match_found:
                break
            filtered_sc_list = set()
            for sc in sc_list:
                if poc.start == sc.OE.annotation.start:
                    filtered_sc_list.add(sc)
                    if poc.end == sc.OE.annotation.end:
                        match_found = True
                        break
                    else:
                        j = i + 1
                        matched = False
                        while j < len(semantic_concepts):
                            sc_list_next = semantic_concepts[j]
                            filtered_next_sc_list = set()
                            for sc_next in sc_list_next:
                                filtered_next_sc_list.add(sc_next)
                                if poc == sc_next.OE.annotation.end:
                                    match_found = True
                                    matched = True
                                    break
                            if filtered_next_sc_list:
                                filtered_ocs.append(list(filtered_next_sc_list))
                            if matched:
                                break
                            j += 1
            if filtered_sc_list:
                filtered_ocs.append(list(filtered_sc_list))
        return filtered_ocs

    def cleanSemanticConcepts(self, q):
        """
        Given an populated Query instance, remove those OCs that overlap its focus if it has maximum priority
        and sort the resulting OCs
        :param q: Query instance
        :return: updated Query object
        """
        focus = q.focus
        if q.semanticConcepts and focus and focus.mainSubjectPriority == POC.MSUB_PRIORITY_MAX:
            new_scs = []
            for sc_list in q.semanticConcepts:
                if sc_list:
                    first_sc = sc_list[0]
                    if first_sc and first_sc.OE and first_sc.OE.annotation:
                        ann = first_sc.OE.annotation
                        if ann.start != focus.start or ann.end != focus.end:
                            #  No overlap --> keep SemanticConcept list
                            new_scs.append(sc_list)
            q.semanticConcepts = sorted(new_scs, cmp=SemanticConceptListCompareOffset)
        return q

    def separatePOCswithJJ(self, pocs):
        """
        Given a list of POCs, split each POC containing an adjective into two new POCs; one containing the adjective
        and one containing everything else
        :param pocs: List of POC instances from a Query
        :return: Updated list of POCs
        """
        newpocs = []
        #  Node tags that indicate an adjective in a pre-terminal POC
        adj_tags = [JJ_TREE_POS_TAG, VBN_TREE_POS_TAG, VBG_TREE_POS_TAG, RBS_TREE_POS_TAG, ADJP_TREE_POS_TAG,
                    JJR_TREE_POS_TAG, JJS_TREE_POS_TAG]
        for poc in pocs:
            others = set()
            adjs = []
            poc_preters = [immutableCopy(t) for t in getSubtreesAtHeight(poc.tree, 2)]
            if len(poc_preters) > 1:
                for preter in poc_preters:
                    if preter.label() in adj_tags:
                        adjs.append(preter)
                    else:
                        others.add(preter)
            else:
                others.add(poc_preters[0])
            if others:
                newpoc = self.updateSplitPOC(poc, [mutableCopy(t) for t in others], poc.tree.label())
                newpocs.append(newpoc)
            if adjs:
                adjpoc = self.updateSplitPOC(poc, [mutableCopy(t) for t in adjs], poc.tree.label())
                newpocs.append(adjpoc)
        return newpocs

    def removeUselessTokens(self, pocs):
        """
        Updates POCs by removing useless tokens at the starting offset e.g. 'which', 'what'...
        If the whole POCs has to be ignored, completely removes it from the input list
        :param pocs: A list of POC instances
        :return: Updated list of POCs
        """
        new_pocs = []
        for poc in pocs:
            newpoc = poc
            children = getSubtreesAtHeight(poc.tree, 2)
            for child in children:
                child_str = quick_norm(treeRawString(child))
                if any(child_str.startswith(s) for s in TOKEN_IGNORE_CONSOLIDATION):
                    ignore = True
                elif child.label() in [PRP_TREE_POS_TAG, PRPDOLLAR_TREE_POS_TAG]:
                    ignore = True
                else:
                    ignore = False
                if ignore:
                    if len(poc.tree) > 1:
                        new_pt = removeSubTree(newpoc.tree, child)
                        newpoc = self.updateSplitPOC(poc, new_pt, poc.tree.label())
                    else:
                        newpoc = None
            if newpoc:
                new_pocs.append(newpoc)
        return new_pocs

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
            newrawtext = ''
            new_tokens = []
            first = True
            for t in new_trees:
                if first:
                    first = False
                    newrawtext += treeRawString(t)
                else:
                    newrawtext += ' ' + treeRawString(t)
                new_tokens.extend(t.leaves())
            newtree = nltk.Tree(root_label, new_trees)
            newPoc = POC(newrawtext, newtree)
            newPoc.start_original = poc.start
            newPoc.end_original = poc.end
            newPoc.start, newPoc.end = Consolidator.getSplitPOCOffsets(poc, new_tokens)
            newPoc.head = poc.head
            newPoc.modifiers = poc.modifiers
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
        new_start = poc.start + start_delay
        new_end = poc.end - end_delay
        return new_start, new_end
