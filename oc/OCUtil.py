import Ontovis.constants as o_c
from NLP.model.OE import *
from NLP.model.SemanticConcept import *


def preConsolidateQuery(q, o):
    """
    Removes redundant OCs and POCs of a given query with information from the ontology
    :param q: A fully instantiated Query object
    :param o: A loaded ontology
    :return: A pre-consolidated Query instance
    """
    filtered_anns, removed_anns = filterInstancesOfClass(q.annotations, o)
    pocs_clean = []
    for poc in q.pocs:
        for ann in removed_anns:
            if poc.start != ann.start and poc.end != ann.end and poc.rawText != ann.rawText:
                pocs_clean.append(poc)
    q.pocs = pocs_clean
    q.annotations = sorted(filtered_anns, cmp=AnnotationsCompareOffset)
    return q

def filterInstancesOfClass(annotations, o):
    """
    Given a list of Annotation, removes those who are classes if there are instances right next to them (to the left
    or to the right) in the query (e.g. if a query contains 'the Nile river', river should be removed)
    :param annotations: an Annotation list
    :param o: an instantiated ontology
    :return: tuple (list<Annotation>,list<Annotation>): (filtered, unsorted, list of Annotation, removed annotations)
    """
    to_remove = set()
    annotations_with_start = {}
    for ann in annotations:
        if ann.start not in annotations_with_start:
            annotations_with_start[ann.start] = []
        annotations_with_start[ann.start].append(ann)
    # Clean class-instance or instance-class pairs
    ann_starts = annotations_with_start.keys()
    for i in ann_starts:
        next_start = i+1
        if next_start in ann_starts:
            anns_current = annotations_with_start[i]
            anns_next = annotations_with_start[next_start]
            to_remove |= removeNeighborAnnotation(anns_current, anns_next, o)
            to_remove |= removeNeighborAnnotation(anns_next, anns_current, o)
    return [a for a in annotations if a not in to_remove], list(to_remove)


def removeNeighborAnnotation(first_annotations, second_annotations, o):
    to_remove = set()
    first_classes = [a1 for a1 in first_annotations if o_c.OTYPE_CLASS in a1.oc_type]
    second_instances = [a2 for a2 in second_annotations if o_c.OTYPE_IND in a2.oc_type]
    for c in first_classes:
        c_uri = c.oc_type[o_c.OTYPE_CLASS]
        for inst in second_instances:
            i_uri = inst.oc_type[o_c.OTYPE_IND]
            if o.instanceIsOfClass(o.stripNamespace(i_uri), o.stripNamespace(c_uri)):
                to_remove.add(c)
    return to_remove


def removeOverlappingAnnotations(annotations):
    """
    Given a list of annotations, removes those which are contained within already existing ones
    :param annotations: a list of Annotation instances
    :return: a list of non-overlapping Annotation instances
    """
    sorted_anns = set(sorted(annotations, cmp=AnnotationsCompareOffset))
    visited = []
    to_remove = set()
    for a in sorted_anns:
        if a not in visited:
            visited.append(a)
            for b in sorted_anns:
                if b not in visited and a.overlaps(b):
                    to_remove.add(b)
                    visited.append(b)
    return list(sorted_anns - to_remove)


def removeSimilarAnnotations(annotations):
    """
    Given a list of annotations, removes those which are more or less equal to each other according to
    the equalsNonStrict method.
    :param annotations: a list of Annotation instances
    :return: a list of distinct Annotation instances
    """
    i = 0
    to_remove = set()
    while i < len(annotations):
        j = i + 1
        while j < len(annotations):
            if annotations[i].equalsNonStrict(annotations[j]):
                to_remove.add(annotations[j])
            j += 1
        i += 1
    return list(set(annotations) - to_remove)


def appendOntologyNoneElements(semantic_concepts):
    """
    Appends an OntologyNoneElement to each list of overlapped semantic concepts
    :param semantic_concepts: list<list<SC>>: overlapped SCs, where the first one in each sub-list overlaps the rest
    :return: The input list with a new appended OntologyNoneElement on each sub-list
    """
    for overlapping_scs in semantic_concepts:
        for sc in overlapping_scs:
            if sc.OE and type(sc.OE) is not OntologyNoneElement and sc.OE.annotation:
                sem_none = SemanticConcept()
                ann_copy = sc.OE.annotation.deepcopy()
                o_none = OntologyNoneElement()
                o_none.annotation = ann_copy
                sem_none.OE = o_none
                overlapping_scs.append(sem_none)
                break  # Consider only the first OE with an annotation
    return overlapping_scs


def AnnotationsCompareOffset(ann1, ann2):
    """
    Returns whether one annotation appears before another
    :param ann1: first Annotation instance
    :param ann2: second Annotation instance
    :return: a positive number if ann1 appears before ann2, zero if both annotations appear in the same position,
    a negative number otherwise. Overlapping annotations are considered to appear before overlapped annotations if they
    start on the same offset.
    """
    if ann1 and ann2:
        if ann1.start >= 0 and ann2.start >= 0:
            offset = ann1.start - ann2.start
            if offset == 0:
                offset = ann2.end - ann1.end
        elif ann2.start < 0:
            offset = 1
        else:
            offset = -1
    elif ann1:
        offset = 1
    else:
        offset = -1
    return offset


def SemanticConceptListCompareOffset(sem_list_1, sem_list_2):
    """
    Returns whether one list of overlapping semantic concepts appears before another one by comparing the annotations
    of their main overlapping OEs
    :param sem_list_1: first SemanticConcept instance list
    :param sem_list_2: second SemanticConcept instance list
    :return: a positive number if sem_list_1 appears before sem_list_2 according to their main overlapping OEs
    """
    if sem_list_1 and sem_list_2:
        ann1 = sem_list_1[0].OE.annotation
        ann2 = sem_list_2[0].OE.annotation
        if ann1.start >= 0 and ann2.start >= 0:
            offset = ann1.start - ann2.start
            if offset == 0:
                offset = ann1.end - ann2.end
        elif ann2.start < 0:
            offset = 1
        else:
            offset = -1
    elif sem_list_1:
        offset = 1
    else:
        offset = -1
    return offset
