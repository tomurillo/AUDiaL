import nltk
from NLP.constants import *

ROOT = 'ROOT'


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
    Tries to find the head of a noun phrase
    TODO: Improve it according to Collins 1999, Appendix A
    :param ptree: an nltk.Tree parse tree
    :return: POC: the inferred head of the phrase
    """
    from NLP.model.POC import POC
    noun_labels = [NN_TREE_POS_TAG, NNS_TREE_POS_TAG, NNP_TREE_POS_TAG, NNPS_TREE_POS_TAG]
    top_trees = [child for child in ptree if isinstance(child, nltk.Tree)]
    top_nouns = [t for t in top_trees if t.label() in noun_labels]
    head_poc = POC()
    if len(top_nouns) > 0:
        head_poc.rawText = top_nouns[-1][0]
        head_poc.tree = top_nouns[-1]
    else:
        top_nps = [t for t in top_trees if t.label() == NP_TREE_POS_TAG]
        if len(top_nps) > 0:
            head_poc.rawText = top_nps[-1][0]
            head_poc.tree = top_nps[-1]
        else:
            nouns = [p for p in getSubtreesAtHeight(ptree, 2) if p.label() in noun_labels]
            if len(nouns) > 0:
                head_poc.rawText = nouns[-1][0]
                head_poc.tree = nouns[-1]
            else:
                head_poc.tree = getSubtreesAtHeight(ptree, 2)[-1]
                head_poc.rawText = head_poc.tree[0]
    return head_poc


def getModifiersOfNounPhrase(ptree):
    """
    Returns a list of parse trees with the modifiers of the given NP
    :param ptree: an nltk.Tree parse tree whose root's label is 'NP'
    :return: list<nltk.Tree>: inferred Modifiers
    """
    modif = []
    noun_labels = [NN_TREE_POS_TAG, NNS_TREE_POS_TAG, NNP_TREE_POS_TAG, NNPS_TREE_POS_TAG, NP_TREE_POS_TAG]
    if type(ptree) is nltk.Tree and ptree.label() == NP_TREE_POS_TAG:
        modif = [t for t in ptree if t.label() not in noun_labels]
    return modif


def containNodes(ptree, labels):
    """
    Returns whether the given tree contains nodes with any of the given labels
    :param ptree: nltk.Tree parse tree instance
    :param labels: list<string> list of POS tags to be considered
    :return: True if the tree contains any of the labels, False otherwise
    """
    contains = False
    if type(ptree) is nltk.Tree and labels:
        if ptree.label() in labels:
            contains = True
        else:
            contains = any(containNodes(child, labels) for child in ptree)
    return contains


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
        if isinstance(leafs, basestring):
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

def distanceBetweenAnnotations(ptree, ann1, ann2):
    """
    Returns the distance between the parse trees of the two given annotations or POCs
    :param ptree: a Parse Tree of a user's query
    :param ann1: Annotation or POC instance
    :param ann2: Annotation or POC instance
    :return: int; Node distance between the leftmost leaf of ann1 and the rightmost leaf of ann2
    """
    path = pathBetweenAnnotations(ptree, ann1, ann2)
    if path:
        distance = len(path)
    else:
        distance = float("inf")
    return distance


def pathBetweenAnnotations(ptree, ann1, ann2):
    """
    Returns the path between 2 annotations in a query
    :param ptree: a Parse Tree of a user's query
    :param ann1: Annotation or POC instance
    :param ann2: Annotation or POC instance
    :return: list<str> Path of nodes between the parse trees of ann1 and ann2 in ptree
    """
    path = []
    if ptree and ann1.start > -1 and ann2.end > -1:
        leafs_path = pathBetweenLeafs(ptree, ann1.start, ann2.end)
        root1 = ann1.tree.label()
        i = 0
        while i < len(leafs_path) and leafs_path[i] != root1:
            i += 1
        root2 = ann2.tree.label()
        j = len(leafs_path) - 1
        while j >= 0 and leafs_path[j] != root2:
            j -= 1
        path = leafs_path[i:j+1]
    return path


def treeDepth(ptree):
    """
    Returns the total depth (depth of deepest leaf) of the given Parse Tree
    :param ptree: a Parse Tree
    :return: a tuple (depth (int), deepest leaf (string))
    """
    if not isinstance(ptree, nltk.ParentedTree):
        ptree = toParentedTree(ptree)
    max_depth = -1
    lowest_leaf = None
    for leaf in range(len(ptree.leaves())):
        depth = len(ptree.leaf_treeposition(leaf))
        if depth > max_depth:
            max_depth = depth
            lowest_leaf = leaf
    return max_depth, lowest_leaf


def pathBetweenLeafs(ptree, leaf_index_1, leaf_index_2):
    """
    Returns the path between two given words in a parse tree
    :param ptree: A Parse Tree
    :param leaf_index_1: leaf index of the first word
    :param leaf_index_2: leaf index of the second word
    :return: path between the two words
    """
    if not isinstance(ptree, nltk.ParentedTree):
        ptree = toParentedTree(ptree)
    pos1 = ptree.leaf_treeposition(leaf_index_1)
    pos2 = ptree.leaf_treeposition(leaf_index_2)
    #  Compute least-common ancestor length
    lca_length = 0
    while lca_length < len(pos1) and lca_length < len(pos2) and pos1[lca_length] == pos2[lca_length]:
        lca_length += 1
    # Path from first leaf to lca
    labels1 = lcaPath(ptree, lca_length, pos1)
    result = labels1[1:]  # Remove root
    result = result[::-1]  # Inverse path
    # Path from lca to second leaf
    result = result + lcaPath(ptree, lca_length, pos2)
    return result


def lcaPath(ptree, lca_length, location):
    """
    Returns the path from ptree's root to the given least common ancestor
    :param ptree: A Parse Tree (nltk.ParentedTree instance)
    :param lca_len: Least common ancestor length
    :param location: leaf_treeposition() of a given leaf
    :return: list<str> a list of labels in the path
    """
    labels = []
    for i in range(lca_length, len(location)):
        labels.append(ptree[location[:i]].label())
    return labels


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


def isNumber(ptree):
    """
    Returns whether this tree represents a cardinal number
    :param ptree: nltk.Tree instance
    :return: True if ptree is a cardinal number; False otherwise
    """
    number = False
    if ptree.label() == CD_TREE_POS_TAG:
        number = True
    elif ptree.label() == NP_TREE_POS_TAG:
        for child in ptree:
            if child.label() == CD_TREE_POS_TAG:
                number = True
                break
    return number


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
    elif isinstance(ptree, basestring):
        return ptree
    else:
        raise TypeError("immutableCopy: unknown type given: %s" % str(type(ptree)))


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
    elif isinstance(ptree, basestring):
        return ptree
    else:
        raise TypeError("mutableCopy: unknown type given: %s" % str(type(ptree)))


def toParentedTree(ptree):
    """
    Copies an nltk.Tree instance to a ParentedTree that maintains parent pointers for each node.
    :param ptree: an nltk.Tree instance
    :return: an nltk.ParentedTree instance copied from ptree
    """
    if type(ptree) in [nltk.Tree, nltk.ImmutableTree]:
        return nltk.ParentedTree(ptree.label(), [toParentedTree(c) for c in ptree])
    elif isinstance(ptree, basestring):
        return ptree
    else:
        raise TypeError("toParentedTree: unknown type given: %s" % str(type(ptree)))


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