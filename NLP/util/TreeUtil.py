import nltk
from NLP.constants import *

ROOT = 'ROOT'


def getPocs(ptree):
    """
    Finds POCs (potential ontology concepts) in a parse tree
    See Damljanovic, D. (2011), page 188
    :param ptree: an nltk.Tree parse tree
    :return: List of nltk.Tree
    """
    if not ptree:
        return None
    prepre_labels = [NP_TREE_POS_TAG, NN_TREE_POS_TAG, NX_TREE_POS_TAG, ADJP_TREE_POS_TAG]
    prepre_wh_labels = [WHNP_TREE_POS_TAG, WHADJP_TREE_POS_TAG, WHAVP_TREE_POS_TAG, WHADVP_TREE_POS_TAG]
    child_ignore_labels = [PRP_TREE_POS_TAG, EX_TREE_POS_TAG]
    prepre_pocs = []
    pocs = []
    _, preters, prepreters, allpres = getPrePreTerminals(ptree)
    for subtree in prepreters:
        added = False
        label = subtree.label()
        childlabels = getChildrenLabels(subtree)
        if label and any([label.startswith(l) for l in prepre_labels]):
            add_poc = True
            for child_label in childlabels:
                if any([child_label.startswith(l) for l in child_ignore_labels]):
                    add_poc = False
            if add_poc:
                pocs.append(subtree)
                prepre_pocs.append(subtree)
                added = True
        if label and not added and any([label.startswith(l) for l in prepre_wh_labels]):
            n_children = len(subtree)
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
    # Add preterminals NNs that may have been skipped
    for subtree in preters:
        sub_label = subtree.label()
        if sub_label.startswith(NN_TREE_POS_TAG) or sub_label.startswith(RB_TREE_POS_TAG):
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


def isSubTree(subTree, mainTree):
    """
    Returns whether subTree is contained in mainTree
    :param subTree: an nltk.Tree instance
    :param mainTree: an nltk.Tree instance
    :return: True if subTree is subtree of mainTree; False otherwise
    """
    isSub = False
    if subTree and mainTree:
        if subTree.height() == mainTree.height():
            if subTree == mainTree:
                isSub = True
        elif subTree.height() < mainTree.height():
            for child in mainTree:
                isSub = isSubTree(subTree, child)
                if isSub:
                    break
    return isSub


def getPrePreTerminals(ptree):
    """
    Returns the pre- and pre-preterminal nodes of a given parse tree
    :param ptree: an nltk.Tree parse tree
    :return: tree_depth (int), preterminal trees, pre-preterminal trees (lists of nltk.Tree),
    both prepre- and pre-terminals combined in the same order as they appear in the query
    """
    level_max = 0 # Max depth level reached among all children
    child_levels = [] # Depth of children, starting from 0 at leaves
    preters = [] # Preterminal trees
    prepreters = [] # Pre-preterminal trees
    allpres = [] # Both prepre- and pre-terminals trees
    for child in ptree:
        if isinstance(child, nltk.Tree):
            if child.label() != ROOT:
                level, preters_child, prepreters_child, all_child = getPrePreTerminals(child)
                preters += preters_child
                prepreters += prepreters_child
                allpres += all_child
                child_levels.append(level)
                level += 1
                if level > level_max:
                    level_max = level
        else:
            if level_max == 0:
                level_max = 1
            child_levels.append(0)
    child_levels_set = set(child_levels)
    if len(child_levels_set) > 0:
        first_child_depth = next(iter(child_levels_set))
    else:
        first_child_depth = 0
    if len(ptree) == 1 and first_child_depth == 0:
        preters.append(ptree)
        allpres.append(ptree)
    if len(child_levels_set) == 1 and first_child_depth == 1:
        prepreters.append(ptree)
        allpres.append(ptree)
    return level_max, preters, prepreters, allpres


def getSubtreesAtHeight(ptree, height):
    """
    Returns a list of subtrees of the given trees at the given height
    :param ptree: nltk.Tree parse tree
    :param height: int, root height e.g. 2 to fetch pre-terminal subtrees
    :return: list of nltk.Tree
    """
    subtrees = []
    if isinstance(ptree, nltk.Tree):
        subtrees = [t for t in ptree.subtrees(lambda ptree: ptree.height() == height)]
    return subtrees


def getHeadOfNounPhrase(ptree):
    """
    Tries to find the head of a noun phrase of the given types (labels)
    TODO: Improve it according to Collins 1999, Appendix A
    :param ptree: an nltk.Tree parse tree
    :return: String: the inferred head of the phrase
    """
    noun_labels = [NN_TREE_POS_TAG, NNS_TREE_POS_TAG, NNP_TREE_POS_TAG, NNPS_TREE_POS_TAG]
    top_trees = [ptree[i] for i in range(len(ptree)) if isinstance(ptree[i], nltk.Tree)]
    top_nouns = [t for t in top_trees if t.label() in noun_labels]
    if len(top_nouns) > 0:
        head = top_nouns[-1][0]
    else:
        top_nps = [t for t in top_trees if t.label() == NP_TREE_POS_TAG]
        if len(top_nps) > 0:
            head = top_nps[-1][0]
        else:
            nouns = [p[0] for p in ptree.pos() if p[1] in noun_labels]
            if len(nouns) > 0:
                head = nouns[-1]
            else:
                head = ptree.leaves()[-1]
    return head


def getModifiersOfNounPhrase(ptree):
    """
    Returns a list of parse trees with the modifiers of the given NP
    :param ptree: an nltk.Tree parse tree whose root's label is 'NP'
    :return: list<nltk.Tree>: inferred Modifiers
    """
    modif = []
    noun_labels = [NN_TREE_POS_TAG, NNS_TREE_POS_TAG, NNP_TREE_POS_TAG, NNPS_TREE_POS_TAG, NP_TREE_POS_TAG]
    if isinstance(ptree, nltk.Tree) and ptree.label() == NP_TREE_POS_TAG:
        modif = [t for t in ptree if t.label() not in noun_labels]
    return modif


def removeSubElementFromTree(ptree, tag):
    """
    Returns the a copy of the given parse tree with sub-elements of the given type (tag) removed
    :param ptrees: nltk.Tree
    :param tag: String with a tag e.g. 'DT'
    :return: nltk.Tree
    """
    if isinstance(ptree, nltk.Tree):
        filtered_children = [ct for ct in ptree if type(ct) is not nltk.Tree or ct.label() != tag]
        return nltk.Tree(ptree.label(), [removeSubElementFromTree(c, tag) for c in filtered_children])
    else:
        return ptree

def removeSubTree(ptree, subtree):
    """
    Returns a copy of the given tree without the instances of the given subtree
    :param ptree: an nltk.Tree
    :param subtree: subtree to remove
    :return: copy of ptree without any instances of subtree
    """
    if isinstance(ptree, nltk.Tree):
        filtered_children = [ct for ct in ptree if type(ct) is not nltk.Tree or ct != subtree]
        return nltk.Tree(ptree.label(), [removeSubTree(c, subtree) for c in filtered_children])
    else:
        return ptree


def removeLeafs(ptree, leafs):
    """
    Returns a copy of the given tree without the leaves having any of the given texts
    :param ptree: an nltk.Tree
    :param leafs: list<str>: a list of lowercase strings to consider or a single string
    :return: copy of ptree without any leaves of the given list
    """
    if leafs and isinstance(ptree, nltk.Tree):
        if type(leafs) == str or type(leafs) == unicode:
            leafs = [leafs]
        p_clean = ptree.copy(deep=True)
        preters = getSubtreesAtHeight(ptree, 2)  # Pre-terminals have exactly one leaf
        for pt in preters:
            pt_str = treeRawString(pt).lower().strip()
            if any(s == pt_str for s in leafs):
                p_clean = removeSubTree(p_clean, pt)
        return p_clean
    else:
        return ptree


def getChildrenLabels(ptree):
    """
    Return the labels of the given parse tree's children (non-recursive)
    :param ptree: an nltk.Tree parse tree
    :return: list<string>
    """
    labels = []
    if isinstance(ptree, nltk.Tree):
        labels = [t.label() for t in ptree]
    return labels


def getLabeledSubTrees(ptree, label):
    """
    Fetch labeled subtrees of the given parse tree
    :param ptree: A Parse Tree
    :param label: A label e.g. 'VB', 'VP' or 'NP'
    :return: List of trees with the given label in the root
    """
    return list(ptree.subtrees(filter=lambda x: x.label() == label))


def treeRawString(ptree):
    """
    Returns the text generated by a parse tree
    :param ptree: A Parse Tree
    :return: a string with the tree leaves (raw text)
    """
    raw = ''
    if ptree and isinstance(ptree, nltk.Tree):
        raw = ' '.join(ptree.leaves())
    return raw


def immutableCopy(ptree):
    """
    Create an immutable copy of a Parse Tree. Needed when a PT has to be hashable, for instance to be used as a key
    in a dictionary
    :param ptree: an nltk.Tree instance
    :return: an nltk.ImmutableTree instance copied from ptree
    """
    if type(ptree) is nltk.ImmutableTree:
        return ptree.copy()
    elif type(ptree) is nltk.Tree:
        return nltk.ImmutableTree(ptree.label(), [immutableCopy(c) for c in ptree])
    elif type(ptree) is str or type(ptree) is unicode:
        return ptree
    else:
        raise TypeError("immutableCopy: unknown type given")


def mutableCopy(ptree):
    """
    Copies an immutable tree into a normal nltk.Tree instance
    :param ptree: an nltk.ImmutableTree instance
    :return: an nltk.Tree instance copied from ptree
    """
    if type(ptree) is nltk.ImmutableTree:
        return nltk.Tree(ptree.label(), [mutableCopy(c) for c in ptree])
    elif type(ptree) is nltk.Tree:
        return ptree.copy()
    elif type(ptree) is str or type(ptree) is unicode:
        return ptree
    else:
        raise TypeError("mutableCopy: unknown type given")


def printTree(ptree):
    """
    Prints a parse tree
    :param ptree: A Parse Tree
    :return: A string representation of the tree
    """
    out = ""
    for node in ptree:
        if isinstance(node, nltk.Tree):
            if node.label() == 'S':
                out += "======== Sentence =========\n"
                out += "Sentence:" + " ".join(node.leaves()) + "\n"
            else:
                out += "Label:" + node.label() + "\n"
                out += "Leaves:" + str(node.leaves()) + "\n"
            out += printTree(node)
        else:
            out += "Word:" + node + "\n"
    return out


def quick_norm(phrase):
    """
    Simple string normalization
    :param word: string
    :return: stripped, lowercase string
    """
    if phrase:
        return phrase.strip().lower()
    else:
        return ''


def positionsInList(longer_list, shorter_list):
    """
    Returns a list with the positions in which shorter_list appears in longer_list
    :param longer_list:
    :param small_list:
    :return: A list of <int, int> tuples the indexes of the occurrences
    """
    pos = []
    for i in xrange(len(longer_list)-len(shorter_list)+1):
        k = 0
        for j in xrange(len(shorter_list)):
            if longer_list[i+j] != shorter_list[j]:
                break
            else:
                k += 1
        if k == len(shorter_list):
            pos.append((i, i+k-1))
    return pos