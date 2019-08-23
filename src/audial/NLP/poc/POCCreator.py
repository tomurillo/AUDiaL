from NLP.model.POC import *
from const import *
from NLP.util.TreeUtil import *


class POCCreator(object):
    """
    Finds Potential Ontology Concepts (POCs) in a user's query
    """
    def __init__(self, query):
        """
        POCCreator class constructor
        :param query: A query instance with a parse tree of a user's query
        """
        self.q = query

    def generatePOCs(self):
        """
        Populate a query's POCs
        :return: None; update this instance's query object
        """
        pocs = []
        p_pocs = self.getPocTrees()
        if p_pocs:
            query_token_list = self.q.pt.leaves()
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
                # Update head POC
                head.start, head.end = getSplitPOCOffsets(poc, head.tree.leaves())
                head.start_original = head.start
                head.end_original = head.end
                poc.head = head
        self.q.pocs = pocs

    def getPocTrees(self):
        """
        Finds POCs (potential ontology concepts) subtrees of a parse tree
        :return: List of nltk.Tree
        """
        if not self.q.pt:
            return None
        prepre_labels = [NP_TREE_POS_TAG, NN_TREE_POS_TAG, NX_TREE_POS_TAG, ADJP_TREE_POS_TAG]
        prepre_wh_labels = [WHNP_TREE_POS_TAG, WHADJP_TREE_POS_TAG, WHAVP_TREE_POS_TAG, WHADVP_TREE_POS_TAG]
        child_ignore_labels = [PRP_TREE_POS_TAG, EX_TREE_POS_TAG]
        prepre_pocs = []
        pocs = []
        _, preters, prepreters, allpres = getPrePreTerminals(self.q.pt)
        for subtree in prepreters:
            added = False
            label = subtree.label()
            childlabels = getChildrenLabels(subtree)
            if label and any(label.startswith(l) for l in prepre_labels):
                add_poc = True
                for child_label in childlabels:
                    if any(child_label.startswith(l) for l in child_ignore_labels):
                        add_poc = False
                if add_poc:
                    pocs.append(subtree)
                    prepre_pocs.append(subtree)
                    added = True
            if label and not added and any(label.startswith(l) for l in prepre_wh_labels):
                n_children = len(subtree)
                first_child, second_child, fchild_label, schild_label = (None,) * 4
                if n_children > 0:
                    tree_iter = iter(subtree)
                    first_child = tree_iter.next()
                    fchild_label = first_child.label()
                if n_children > 1:
                    second_child = tree_iter.next()
                    schild_label = second_child.label()
                if n_children == 1:
                    if fchild_label.startswith(WRB_TREE_POS_TAG) or fchild_label.startswith(WP_TREE_POS_TAG):
                        for leaf in first_child:
                            leaf_label = quick_norm(leaf)
                            if leaf_label in ['where', 'when', 'who']:
                                pocs.append(subtree)
                                prepre_pocs.append(subtree)
                elif n_children == 2:
                    if fchild_label.startswith(WRB_TREE_POS_TAG) and (schild_label.startswith(JJ_TREE_POS_TAG) or
                                                                      schild_label.startswith(ADJP_TREE_POS_TAG)):
                        pocs.append(subtree)
                        prepre_pocs.append(subtree)
                    elif schild_label.startswith(NN_TREE_POS_TAG) or schild_label.startswith(NP_TREE_POS_TAG):
                        pocs.append(subtree)
                        prepre_pocs.append(subtree)
                    elif fchild_label.startswith(NN_TREE_POS_TAG) or fchild_label.startswith(NP_TREE_POS_TAG) or \
                            fchild_label.startswith(RB_TREE_POS_TAG):
                        pocs.append(subtree)
                        prepre_pocs.append(subtree)
                elif n_children > 2:
                    for child in subtree:
                        sub_label = quick_norm(child.label())
                        if sub_label.startswith(NP_TREE_POS_TAG) or sub_label.startswith(NN_TREE_POS_TAG):
                            pocs.append(child)
                            prepre_pocs.append(subtree)
        # Add preterminals NNs and VBs that may have been skipped
        for subtree in preters:
            sub_label = subtree.label()
            if (sub_label.startswith(NN_TREE_POS_TAG) or not self.ignoreAdverbPOC(subtree) or
                    not self.ignoreVerbPOC(subtree)):
                already_poc = False
                # Check whether potential POC has already been covered by a pre-preterminal
                for prepre_poc in prepre_pocs:
                    already_poc = isSubTree(subtree, prepre_poc)
                    if already_poc:
                        break
                if not already_poc:
                    pocs.append(subtree)
        # Sort results as they appear in query
        sorted_pocs = [s for s in allpres if s in pocs]
        return sorted_pocs

    def ignoreVerbPOC(self, subtree):
        """
        Given a word-level parse tree of a verb, return whether it should be ignored by the POC finder
        :param subtree: nltk.Tree instance (pre-terminal tree) with a VB*-labeled root
        :return: True if the tree needs not be taken as a POC; False otherwise
        """
        ignore = True
        if subtree:
            label = subtree.label()
            if label and label.startswith(VB_TREE_POS_TAG):
                text = quick_norm(treeRawString(subtree))
                if text not in TASK_IGNORE:
                    ignore = False
        return ignore

    def ignoreAdverbPOC(self, subtree):
        """
        Given a word-level parse tree of an adverb, return whether it should be ignored by the POC finder
        :param subtree: nltk.Tree instance (pre-terminal tree) with a RB*-labeled root
        :return: True if the tree needs not be taken as a POC; False otherwise
        """
        ignore = True
        if subtree:
            label = subtree.label()
            if label and label.startswith(RB_TREE_POS_TAG):
                text = quick_norm(treeRawString(subtree))
                if text not in RB_IGNORE:
                    ignore = False
        return ignore
