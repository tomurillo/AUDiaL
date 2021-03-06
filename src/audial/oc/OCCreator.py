from flask import session
from const import SESS_USER_LABELS
import ontology.constants as o_c
from NLP.model.OE import *
from NLP.model.SemanticConcept import *
from NLP.util.TreeUtil import quick_norm
from OCUtil import SemanticConceptListCompareOffset


def addSemanticConcepts(q, sess_id):
    """
    Add a list of semantic concepts to a Query instance
    :param q: A Query instance with annotations
    :param sess_id: string; prefix of user session variables
    :return: Updated query instance
    """
    query_anns = q.annotations
    q.semanticConcepts = getSemanticConcepts(query_anns, sess_id)
    return q


def getSemanticConcepts(annotations, sess_id=None, add_none=False):
    """
    Converts annotations to semantic concepts
    :param annotations: An offset-sorted list of Annotation
    :param sess_id: string; prefix of user session variables
    :param add_none: Whether to add None Semantic Concepts to the output lists
    :return: list<list<SemanticConcept>>: a list of overlapped semantic concepts by text, where the first SC of each
    list is the overlapping one.
    """
    overlapped_anns = getOverlappedAnnotations(annotations)
    #  Create OEs from overlapped Annotations
    overlapped_oes = getOverlappedOntologyElements(overlapped_anns, sess_id)
    #  Group overlapped OEs by text
    overlapped_by_text = getOverlappedOntologyElementsGroupByText(overlapped_oes)
    #  Group overlapping instances of the same class under one OE
    overlapped_and_grouped = groupInstancesOfSameClass(overlapped_by_text)
    sem_concepts = []
    for oe_list in overlapped_and_grouped:
        sem_overlapped = []
        for oe in oe_list:
            sem_con = SemanticConcept()
            sem_con.OE = oe
            sem_overlapped.append(sem_con)
        sem_concepts.append(sem_overlapped)
    sorted_sems = sorted(sem_concepts, cmp=SemanticConceptListCompareOffset)
    if add_none:
        return appendOntologyNoneElements(sorted_sems)
    return sorted_sems


def getOverlappedOntologyElements(nested_annotations, sess_id=None):
    """
    Creates Ontology Elements according to a given list of overlapped annotations
    :param nested_annotations: A dict of Annotation as given by the getOverlappedAnnotations method
    :param sess_id: string; prefix of user session variables
    :return: list<list<SemanticConcept>>: a list of overlapped OEs where the first OEs of each
    list are the overlapping ones.
    """
    oelements = []
    for ann, overlapped_anns in nested_annotations.iteritems():
        ov_oe_list = []
        ov_oe_list.extend(annotationToOntologyElements(ann, sess_id))
        for ov_ann in overlapped_anns:
            ov_oe_list.extend(annotationToOntologyElements(ov_ann, sess_id))
        oelements.append(ov_oe_list)
    return oelements


def annotationToOntologyElements(annotation, sess_id=None):
    """
    Creates Ontology Elements according to a given annotation
    :param annotation: Annotation instance
    :param sess_id: string; prefix of user session variables
    :return: list<OntologyElement> instances
    """
    oe_list = []
    if annotation and annotation.oc_type:
        literal_instances = {}
        for ann_type in annotation.oc_type:
            oe = None
            if ann_type == o_c.OTYPE_CLASS:
                oe = OntologyEntityElement()
                if 'class_specScore' in annotation.extra:
                    oe.specificity = annotation.extra['class_specScore']
            elif ann_type == o_c.OTYPE_IND:
                oe = OntologyInstanceElement()
                oe.uris = [annotation.oc_type[ann_type]]
                if 'classUri' in annotation.extra:
                    oe.classUris = annotation.extra['classUri']
                else:
                    from warnings import warn
                    warn('Orphan instance %s' % annotation.oc_type[ann_type])
                if 'directClassUri' in annotation.extra:
                    oe.classUri = annotation.extra['directClassUri']
            elif ann_type == o_c.OTYPE_OPROP:
                oe = OntologyObjectPropertyElement()
                if 'domain' in annotation.extra:
                    oe.domain = annotation.extra['domain']
                if 'range' in annotation.extra:
                    oe.range = annotation.extra['range']
                if 'prop_specScore' in annotation.extra:
                    oe.specificity_score = annotation.extra['prop_specScore']
                if 'prop_distScore' in annotation.extra:
                    oe.distance_score = annotation.extra['prop_distScore']
            elif ann_type == o_c.OTYPE_DTPROP:
                oe = OntologyDatatypePropertyElement()
                if 'domain' in annotation.extra:
                    oe.domain = annotation.extra['domain']
                if 'range' in annotation.extra:
                    oe.range = annotation.extra['range']
                if 'prop_specScore' in annotation.extra:
                    oe.specificity_score = annotation.extra['prop_specScore']
                if 'prop_distScore' in annotation.extra:
                    oe.distance_score = annotation.extra['prop_distScore']
            elif ann_type == o_c.OTYPE_LITERAL:
                triples_of_literal = annotation.extra['triples']
                # Group according to property
                if triples_of_literal:
                    for s, p, o in triples_of_literal:
                        if p in literal_instances:
                            literal_instances[p].append(s)
                        else:
                            literal_instances[p] = [s]
                    for p, instances in literal_instances.iteritems():
                        lit_oe = OntologyLiteralElement()
                        lit_oe.triples = [(i, p, o) for i in instances]
                        lit_oe.annotation = annotation
                        lit_oe.uri = annotation.oc_type[ann_type]
                        oe_list.append(lit_oe)
            if oe:
                oe.annotation = annotation
                oe.uri = annotation.oc_type[ann_type]
                oe_list.append(oe)
    user_oes = annotationToUserLabel(annotation, sess_id)
    oe_list.extend(user_oes)
    return oe_list


def annotationToUserLabel(annotation, sess_id):
    """
    Checks if the given annotation matches any of the labels declared by the user in the current session. If so,
    creates a new string Literal OE for it.
    :param annotation: Annotation instance
    :param sess_id: string; prefix of user session variables
    :return: list<OntologyLiteralElement> instance if matching user labels found; empty list otherwise
    """
    label_oes = []
    if sess_id and annotation and annotation.rawText:
        ann_text = annotation.rawText
        sess_var = SESS_USER_LABELS % sess_id
        labels = session.get(sess_var, {})
        user_labels = set()
        for e, e_label in labels.iteritems():
            user_labels.update(l for l in e_label.replace(';', ',').split(","))
            user_labels.add(e_label)
        for label in user_labels:
            if quick_norm(label) == ann_text:
                oe = OntologyLiteralElement()
                oe.uri = label
                oe.annotation = annotation
                oe.is_user_label = True
                label_oes.append(oe)
    return label_oes


def getOverlappedAnnotations(annotations):
    """
    Returns which annotations are overlapped by other annotations
    :param annotations: a sorted list of Annotation instances
    :return: dict{Annotation: list<Annotation>}: Key is overlapping Annotation, value is a list of Annotation that
    are overlapped by the key
    """
    overlapped_anns = {}
    added = set()
    i = 0
    while i < len(annotations):
        j = i + 1
        ann1 = annotations[i]
        while j < len(annotations):
            ann2 = annotations[j]
            if ann1.overlaps(ann2):
                overlapping, overlapped = ann1, ann2
            elif ann2.overlaps(ann1):
                overlapping, overlapped = ann2, ann1
            else:
                overlapping, overlapped = None, None
            if overlapping and overlapped and overlapped not in added:
                if overlapping not in overlapped_anns:
                    overlapped_anns[overlapping] = []
                overlapped_anns[overlapping].append(overlapped)
                added.add(overlapping)
                added.add(overlapped)
            j += 1
        if ann1 not in added:  # ann1 does not overlap or is overlapped, add its own empty list to dict
            overlapped_anns[ann1] = []
        i += 1
    return overlapped_anns


def getOverlappedOntologyElementsGroupByText(oelements):
    """
    Given a dict of overlapped ontology elements, splits those overlapped elements that have different underlying
    text into different groups.
    :param oelements: A list of overlapped OEs as given by the getOverlappedOntologyElements method
    :return: list<list<OntologyElement>> A list with overlapping OEs (lists of OEs) that have the same
    underlying text. The first element of each sub-list is the overlapping OE.
    """
    overlapped_oe_by_text = []
    for overlapped_oes in oelements:
        text_overlaps = {}  # Key is text, value is list of overlapping OEs with that text
        for oe in overlapped_oes:
            oe_text = oe.annotation.text
            if oe_text in text_overlaps:
                text_overlaps[oe_text].append(oe)
            else:
                text_overlaps[oe_text] = [oe]
        for text in text_overlaps:
            oes_with_text = text_overlaps[text]
            overlapped_oe_by_text.append(oes_with_text)
    return overlapped_oe_by_text


def groupInstancesOfSameClass(oelements):
    """
    Given a dict of overlapped-by-text ontology elements (OE), combines overlapping OEs which are instance of the
    same class(es) into a single OE containing all instances
    :param oelements: A list of overlapped OEs as given by the getOverlappedOntologyElementsGroupByText method
    :return: list<list<OntologyElement>> A list with overlapping OEs (lists of OEs) that have the same
    underlying text. The first element of each sub-list is the overlapping OE. Overlapping instances of the same
    class are represented by a single OntologyInstanceElement.
    """
    final_oes = []
    for overlapped_oes in oelements:
        grouped_oes = []
        instance_groups = {}
        for oe in overlapped_oes:
            if isinstance(oe, OntologyInstanceElement):
                c_str = str(oe.classUris)  # Classes this instance belongs to
                if c_str in instance_groups:
                    instance_groups[c_str].uris.append(oe.uri)  # Group instances under same OE
                else:
                    instances_oe = oe.copy()
                    instances_oe.uris = [oe.uri]
                    instance_groups[c_str] = instances_oe
                    grouped_oes.append(instances_oe)
            else:
                grouped_oes.append(oe)
        final_oes.append(grouped_oes)
    return final_oes


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
    return semantic_concepts
