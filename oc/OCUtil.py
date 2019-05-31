import ontology.constants as o_c
from NLP.util.TreeUtil import distanceBetweenAnnotations
from NLP.model.SemanticConcept import *
from NLP.model.QueryFilter import QueryFilterCardinal
from ontology.bar_chart_ontology import BarChartOntology


def preConsolidateQuery(q, o):
    """
    Removes redundant OCs and POCs of a given query with information from the ontology
    :param q: A fully instantiated Query object
    :param o: A loaded ontology
    :return: A pre-consolidated Query instance
    """
    filtered_anns, removed_anns = filterInstancesOfClass(q.annotations, o)
    pocs_clean = []
    if removed_anns:
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


def removeNeighborAnnotation(first_annotations, second_annotations, o):
    """
    Given two lists of annotations, returns which annotations from the first list need to be removed
    because they are underpinned by classes with instances existing in the annotations of the second list
    :param first_annotations: list<Annotation>
    :param second_annotations: list<Annotation>
    :param o: instantiated Ontology
    :return: list<Annotation>
    """
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


def overlappingOCsVerified(ocs):
    """
    Returns whether the given list of overlapping OCs have been manually disambiguated by the user
    :param ocs: list<SemanticConcept> a list of overlapping (by text) OCs
    :return: True if the OCs have been already verified; False otherwise
    """
    return any(oc.verified for oc in ocs)


def allOCsShareNamespace(scs, ns=None):
    """
    Returns whether all the given OCs share the same namespace
    :param scs: List<List<SemanticConcept>
    :param ns: The namespace to consider; None to fetch the namespace from the OCs themselves
    :return: True if all OCs share the same namespace, false otherwise
    """
    from ontology.util import getNamespace
    shared = True
    for sc_list in scs:
        if not shared:
            break
        if sc_list and isinstance(sc_list[0], SemanticConcept) and sc_list[0].OE and \
                not isinstance(sc_list[0].OE, (OntologyNoneElement, OntologyLiteralElement)):
            for sc in sc_list:
                oe_ns = getNamespace(sc.OE.uri)
                if oe_ns:
                    if not ns:
                        ns = oe_ns
                    elif ns != oe_ns:
                        shared = False
                        break
    return shared


def nextAmbiguousOCs(q):
    """
    Choose which query's OCs must be disambiguated next by the user according to which ones lay the closest
    to the question's focus.
    :param q: a consolidated Query instance
    :return: list<SemanticConcept>: Overlapping OCs that need disambiguation next
    """
    ocs_next = []
    if not q.focus:
        if q.semanticConcepts:
            ocs_next = q.semanticConcepts[0]
    else:
        min_dist = float("inf")
        first = False
        for ocs in q.semanticConcepts:
            if len(ocs) > 1 and not overlappingOCsVerified(ocs):
                if not first:
                    ocs_next = ocs
                    first = False
                first_oc = ocs[0]
                distance_to_focus = distanceBetweenAnnotations(q.pt, first_oc.OE.annotation, q.focus)
                if distance_to_focus < min_dist:
                    ocs_next = ocs
                    min_dist = distance_to_focus
    return ocs_next


def nextPOC(q):
    """
    Chooses which POC from the given question needs to be mapped to an OC next
    :param q: a consolidated Query instance
    :return: POC instance
    """
    next_poc = None
    if q and q.pocs:
        min_dist = float("inf")
        for poc in q.pocs:
            neighbor_scs = findNearestOCsOfPOC(q, poc)
            if neighbor_scs:
                sc = neighbor_scs[0]
                dist = distanceBetweenAnnotations(q.pt, poc, sc.OE.annotation)
                if dist < min_dist:
                    next_poc = poc
                    min_dist = dist
                elif dist == min_dist and next_poc and poc.start > next_poc.start:
                    next_poc = poc
        if next_poc is None:
            next_poc = q.pocs[0]
    return next_poc


def nextFilter(q):
    """
    Chooses which unresolved filter in the query needs to be resolved next
    :param q: a consolidated Query instance
    :return: QueryFilter instance
    """
    next_filter = None
    if q and q.filters:
        for qf in q.filters:
            if isinstance(qf, QueryFilterCardinal):
                if not qf.property and not qf.result:
                    next_filter = qf
                    break
    return next_filter


def findNearestOCsOfPOC(q, poc):
    """
    Returns the nearest ontology resources to the given POC of a user query
    :param q: a consolidated Query instance
    :param poc: POC instance
    :return: List<SemanticConcept> Nearest ontology resources available in the query to the POC
    """
    neighbors = []
    if q and q.semanticConcepts:
        min_dist = float("inf")
        flattened_scs = q.flattened_scs()
        for sc in flattened_scs:
            if type(sc.OE) is not OntologyNoneElement:
                distance = distanceBetweenAnnotations(q.pt, poc, sc.OE.annotation)  # Distance between POC and OC
                if distance < min_dist:
                    neighbors = [sc]
                    min_dist = distance
                elif distance == min_dist:
                    neighbors.append(sc)
    return neighbors


def findNearestOCsInQuery(q, overlapped_ocs, include_none=False):
    """
    Given a list of overlapped OCs, finds the nearest ones in the given query, where the distance between OCs
    is given by the distance of the paths between the parse tree roots.
    :param q: A consolidated Query instance
    :param overlapped_ocs: list<SemanticConcept> with overlapping OCs, where the first OC overlaps the rest
    :param include_none: whether to include OntologyNoneElement instances in the results (default False)
    :return: list<SemanticConcept> nearest OCs
    """
    nearest = []
    if q and q.semanticConcepts and overlapped_ocs:
        first_oc = overlapped_ocs[0]
        min_dist = float("inf")
        for ocs in q.semanticConcepts:
            if ocs != overlapped_ocs:
                for oc in ocs:
                    if type(oc.OE) is not OntologyNoneElement or include_none:
                        dist = distanceBetweenAnnotations(q.pt, first_oc.OE.annotation, oc.OE.annotation)
                        if dist < min_dist:
                            nearest = [oc]
                            min_dist = dist
                        elif dist == min_dist:
                            nearest.append(oc)
    return nearest


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
