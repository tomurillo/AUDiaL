from NLP.util.TreeUtil import *
from NLP.constants import *
from NLP.model.POC import *
from NLP.model.OE import *
from NLP.model.QueryFilter import QueryFilterCardinal
from consolidator.constants import *
from oc.OCUtil import SemanticConceptListCompareOffset


class Consolidator(object):
    """
    Class responsible for mapping a query's POCs into OCs and disambiguating OCs
    """
    def __init__(self, query):
        """
        Consolidator constructor
        :param query: A Query instance
        """
        self.q = query

    def consolidateQuery(self):
        """
        Perform an automatic mapping of POCs into OCs
        :return: A consolidated Query with unresolved POCs and updated OCs
        """
        pocs_no_jj = self.separatePOCswithJJ()
        self.q.pocs = self.removeUselessTokens(pocs_no_jj)
        self.consolidateFilters()
        self.cleanSemanticConcepts()
        self.consolidatePOCsWithOCs()
        return self.q

    def consolidateAnswerType(self):
        """
        Finds the answer type for a Query
        :return: None; updates query instance
        """
        if self.q and self.q.focus and self.q.focus.head:
            answer_type = []
            # Check first for match between an OC and the head of the focus
            for sc_list in self.q.semanticConcepts:
                if sc_list and not isinstance(sc_list[0].OE, OntologyNoneElement):
                    if self.q.focus.head.equalsAnnotation(sc_list[0].OE.annotation):
                        for sc in sc_list:
                            sc.OE.main_subject = True
                            answer_type.append(sc.OE)
                        break
            if not answer_type:
                first_ocs = []
                for sc_list in self.q.semanticConcepts:
                    if sc_list and not isinstance(sc_list[0].OE, OntologyNoneElement):
                        first_ocs = [sc.OE for sc in sc_list]
                        break
                oc_sample = first_ocs[0] if first_ocs else None
                if oc_sample and oc_sample.annotation:
                    add_ocs = True
                    if oc_sample.annotation.end <= self.q.focus.head.start_original:
                        if isinstance(oc_sample, (OntologyObjectPropertyElement, OntologyDatatypePropertyElement)) \
                                and oc_sample.governor:
                            add_ocs = False
                    elif oc_sample.annotation.start < self.q.focus.head.end_original:
                        add_ocs = False
                    if add_ocs:
                        for oc in first_ocs:
                            oc.main_subject = True
                            answer_type.append(oc)
            self.q.answerType = answer_type

    def consolidatePOCsWithOCs(self):
        """
        Given a question, remove those POCs which overlap with any of its OCs or filters and update overlapped OCs with
        information from the POC.
        :return: None; Updates Query attribute
        """
        pocs_clean = []
        i = 0
        while i < len(self.q.pocs):
            poc = self.q.pocs[i]
            add = True  # Add POCs not contained in any OC or filter for dialogue resolution
            matching_ocs = self.matchingOCsOfPOC(poc)
            if matching_ocs:
                add = False
            else:
                matching_filters = self.matchingFiltersOfPOC(poc)
                if matching_filters:
                    add = False
                    for qf in matching_filters:
                        qf.pocs.append(poc)
            if add:
                for scs in self.q.semanticConcepts:
                    if not add:
                        break
                    for j, sc in enumerate(scs):
                        if sc.overlapsPOC(poc):
                            add = False
                            break
                        elif poc.overlapsOC(sc):
                            if j == 0:
                                #  Create new POC without the contained OC
                                new_poc = self.createSubPOC(poc, sc.OE.annotation.tree)
                                if new_poc:
                                    self.q.pocs.append(new_poc)
                                    add = False
                            sc.OE.annotation.tree = immutableCopy(poc.tree)
            if add and not self.tokenIsOrphan(poc):
                pocs_clean.append(poc)
            i += 1
        self.q.pocs = pocs_clean

    def matchingFiltersOfPOC(self, poc):
        """
        Returns which of the query's filters match the given POC (i.e. they overlap the POC)
        :param poc: a POC instance
        :return: list<QueryFilter>: QueryFilter instances of the query matching the given POC
        """
        overlapping_filters = []
        for qf in self.q.filters:
            if qf.annotation.start <= poc.start_original and qf.annotation.end >= poc.end_original:
                overlapping_filters.append(qf)
        return overlapping_filters

    def matchingOCsOfPOC(self, poc):
        """
        Returns which of the query's Semantic Concepts match the given POC (i.e. they have the same start and
        end offsets)
        :param poc: a POC instance
        :return: list<list<SemanticConcept>>: Overlapping OCs of the query matching the given POC
        """
        match_found = False
        filtered_ocs = []
        for i, sc_list in enumerate(self.q.semanticConcepts):  # Overlapping OCs
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
                        while j < len(self.q.semanticConcepts):
                            sc_list_next = self.q.semanticConcepts[j]
                            filtered_next_sc_list = set()
                            for sc_next in sc_list_next:
                                filtered_next_sc_list.add(sc_next)
                                if poc.end == sc_next.OE.annotation.end:
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
            if match_found:
                return filtered_ocs
            else:
                return []

    def cleanSemanticConcepts(self):
        """
        Given an populated Query instance, perform the following actions:
        1. remove those OCs that overlap its focus if it has maximum priority
        2. remove those Literal OCs contained in a query filter
        3. mark those Literal OCs found to be a task verbalization
        4. sort the resulting OCs
        :return: None; updates Query attribute
        """
        focus = self.q.focus
        if self.q.semanticConcepts:
            new_scs = []
            for sc_list in self.q.semanticConcepts:
                add = False
                if sc_list:
                    first_sc = sc_list[0]
                    if first_sc and first_sc.OE and first_sc.OE.annotation:
                        add = True
                        ann = first_sc.OE.annotation
                        ann_txt = quick_norm(ann.text)
                        if ann_txt in TOKEN_IGNORE_DOMAIN:
                            add = False
                        else:
                            for qf in self.q.filters:
                                if qf.overlaps(ann, strict=False):
                                    add = False
                                    break
                        if add:
                            if focus and focus.mainSubjectPriority == POC.MSUB_PRIORITY_MAX:
                                if ann.start == focus.start and ann.end == focus.end:
                                    #  match --> remove SemanticConcept list
                                    add = False
                            else:
                                task = self.semanticConceptIsTask(first_sc)
                                if task:
                                    if not self.q.task:
                                        first_sc.task = task
                                        first_sc.answer = True
                                        self.q.task = first_sc
                                    else:
                                        from warnings import warn
                                        warn('Two tasks (%s and %s) found in query!' % (self.q.task.task, task))
                if add:
                    new_scs.append(sc_list)
            self.q.semanticConcepts = sorted(new_scs, cmp=SemanticConceptListCompareOffset)

    def semanticConceptIsTask(self, sc):
        """
        Discovers whether the given semantic concept is an analytic task to be performed and adds it to the query
        :param sc: SemanticConcept instance
        :return: string; Task URI if found; False otherwise
        """
        task = False
        if isinstance(sc.OE, OntologyLiteralElement):
            for s, p, o in sc.OE.triples:
                if p.endswith("task_has_verbalization"):
                    task = s
                    break
        return task

    def consolidateFilters(self):
        """
        Automatic consolidation of query filters:
        Remove filters containing other filters
        :return: None; updates Query attribute
        """
        to_remove = set()
        for i, f1 in enumerate(self.q.filters):
            j = i + 1
            while j < len(self.q.filters):
                f2 = self.q.filters[j]
                cont = True
                if isinstance(f1, QueryFilterCardinal) and isinstance(f2, QueryFilterCardinal):
                    if f1.overlapsByOperator(f2):
                        to_remove.add(f2)
                        cont = False
                    elif f2.overlapsByOperator(f1):
                        to_remove.add(f1)
                        cont = False
                if cont:
                    if f1.overlaps(f2, strict=False):
                        to_remove.add(f1)
                    elif f2.overlaps(f1, strict=False):
                        to_remove.add(f2)
                j += 1
        new_filters = [f for f in self.q.filters if f not in to_remove]
        self.q.filters = new_filters

    def removeDuplicatedSemanticConcepts(self):
        """
        Get rid of SemanticConcepts sharing the same URI
        :return: List<List<SemanticConcept>: updated semantic concepts without duplicated URIs
        """
        uris_found = []
        clean_scs = []
        for sc_list in self.q.semanticConcepts:
            found = False
            for sc in sc_list:
                if sc.OE:
                    uri_str = sc.OE.print_uri()
                    if uri_str not in uris_found:
                        uris_found.append(uri_str)
                    else:
                        found = True
                        break
            if not found:
                clean_scs.append(sc_list)
        return clean_scs

    def separatePOCswithJJ(self):
        """
        Split each POC of the query containing an adjective into two new POCs; one containing the adjective
        and one containing everything else
        :return: Updated list of POCs
        """
        newpocs = []
        #  Node tags that indicate an adjective in a pre-terminal POC
        adj_tags = [JJ_TREE_POS_TAG, VBN_TREE_POS_TAG, VBG_TREE_POS_TAG, RBS_TREE_POS_TAG, ADJP_TREE_POS_TAG,
                    JJR_TREE_POS_TAG, JJS_TREE_POS_TAG]
        for poc in self.q.pocs:
            others = []
            adjs = []
            poc_preters = [immutableCopy(t) for t in getSubtreesAtHeight(poc.tree, 2)]
            if len(poc_preters) > 1:
                for preter in poc_preters:
                    if preter.label() in adj_tags:
                        adjs.append(preter)
                    else:
                        others.append(preter)
            elif poc_preters:  # Stray DETs may have an empty parse tree; ignore those
                others.append(poc_preters[0])
            if others:
                newpoc = self.updateSplitPOC(poc, [mutableCopy(t) for t in others], poc.tree.label())
                newpocs.append(newpoc)
            if adjs:
                adjpoc = self.updateSplitPOC(poc, [mutableCopy(t) for t in adjs], poc.tree.label())
                newpocs.append(adjpoc)
        return newpocs

    def tokenIsOrphan(self, poc):
        """
        Returns whether the given POC is an orphan preposition, conjunction, determiner, or other word-level element
        that cannot be a POC
        :param poc: POC instance
        :return:
        """
        orphan = False
        if isinstance(poc, POC) and len(poc.tree) == 1:
            orphan_ignore_labels = [CC_TREE_POS_TAG, DT_TREE_POS_TAG, IN_TREE_POS_TAG, EX_TREE_POS_TAG, MD_TREE_POS_TAG,
                                    TO_TREE_POS_TAG, WPDOLLAR_TREE_POS_TAG, LS_TREE_POS_TAG]
            preters = getSubtreesAtHeight(poc.tree, 2)
            if preters:
                if len(preters) == 1:
                    orphan = preters[0].label() in orphan_ignore_labels
            else:
                orphan = True
        return orphan

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
                poc_txt = quick_norm(newpoc.rawText)
                if poc_txt not in TOKEN_IGNORE_DOMAIN:
                    new_pocs.append(newpoc)
        return new_pocs

    @staticmethod
    def createSubPOC(poc, sub_tree):
        """
        Create a new POC from another one by removing one of its subtrees
        :param poc: POC instance
        :param sub_tree: nltk.Tree; subtree to remove from POC
        :return: POC instance
        """
        new_poc = None
        new_tree = removeSubTree(poc.tree, mutableCopy(sub_tree))
        if new_tree and isinstance(new_tree, nltk.Tree) and sub_tree.height() < poc.tree.height():
            new_poc = POC(treeRawString(new_tree), new_tree)
            new_poc.start_original = poc.start_original
            new_poc.end_original = poc.end_original
            new_poc.start, new_poc.end = getSplitPOCOffsets(poc, new_tree.leaves())
            new_poc.head = poc.head
            new_poc.modifiers = poc.modifiers
            new_poc.mainSubjectPriority = poc.mainSubjectPriority
        return new_poc

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
            newPoc.start, newPoc.end = getSplitPOCOffsets(poc, new_tokens)
            newPoc.head = poc.head
            newPoc.modifiers = poc.modifiers
            newPoc.mainSubjectPriority = poc.mainSubjectPriority
        return newPoc

    def resolveFilterSubject(self, q_filter, ocs):
        """
        Resolve to what element of the query a filter refers to
        :param q_filter: QueryFilterCardinal instance being resolved
        :param ocs: list<mixed<SemanticConcept; POC>> Property OCs or POC that was chosen as the subject of the filter
        :return: updated Query
        """
        if self.q and self.q.filters:
            new_filters = [f for f in self.q.filters if f != q_filter]
            for oc in ocs:
                if isinstance(oc, POC):
                    q_filter.result = True  # Subject is the question's focus
                else:
                    q_filter.property = oc  # Subject is a datatype property
            new_filters.append(q_filter)
            self.q.filters = new_filters
            return self.q

    def resolvePOCtoOC(self, poc, ocs):
        """
        Updates the query object after the user has resolved a POC, mapping it to a OC
        :param poc: resolved POC instance
        :param ocs: list<SemanticConcepts>; OCs the POC has been resolved to
        :return: Updated Query
        """
        try:
            if self.q and poc and ocs:
                self.q.pocs.remove(poc)
                for sc in ocs:
                    sc.verified = True
                    sc_ann = Annotation()
                    sc_ann.populateFromPOC(poc)
                    sc.OE.annotation = sc_ann
                    if sc.task and sc.answer:
                        self.q.task = sc
                self.q.semanticConcepts.append(ocs)
        except ValueError:
            import sys
            print('Warning: resolved POC could not be found in query!', sys.stderr)
        finally:
            return self.q

    def disambiguateOCs(self, ocs):
        """
        Perfoms the manual disambiguation between OCs after a dialogue
        :param q: Query instance
        :param ocs: list<SemanticConcept>; chosen OCs i.e. those that will be kept in the query
        :return: updated Query
        """
        if self.q and ocs:
            chosen_task = False
            new_q_scs = {}
            for sc in ocs:
                if sc.task and sc.answer:
                    chosen_task = True
                oe = sc.OE
                for i, q_sc_overlapped in enumerate(self.q.semanticConcepts):
                    clean_overlapped_scs = new_q_scs.get(i, set())
                    for q_sc in q_sc_overlapped:
                        q_oe = q_sc.OE
                        if q_oe == oe:
                            clean_overlapped_scs.add(q_sc)
                    new_q_scs[i] = clean_overlapped_scs
            disambiguated_scs = []
            for j, q_sc_overlapped in enumerate(self.q.semanticConcepts):
                clean_overlapped_scs = new_q_scs.get(j, set())
                if clean_overlapped_scs:
                    disambiguated_scs.append(list(clean_overlapped_scs))
                    if not chosen_task:
                        for q_sc in q_sc_overlapped:
                            if q_sc.answer and q_sc.task and self.q.task == q_sc:
                                self.q.task = None
                                break
                else:
                    disambiguated_scs.append(q_sc_overlapped)  # Keep these OCs as they are unrelated to the dialogue
            if chosen_task:
                self.q.task = ocs[0]
            self.q.semanticConcepts = disambiguated_scs
            self.consolidatePOCsWithOCs()
            return self.q
