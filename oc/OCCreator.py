import Ontovis.constants as o_c
from NLP.model.OE import *
from NLP.model.SemanticConcept import *
from OCUtil import SemanticConceptListCompareOffset, appendOntologyNoneElements


def getSemanticConcepts(self, annotations, add_none=False):
    """
    Converts annotations to semantic concepts
    :param annotations: An offset-sorted list of Annotation
    :param add_none: Whether to add None Semantic Concepts to the output lists
    :return: list<list<annotation>>: a list of overlapped semantic concepts by text, where the first SC of each
    list is the overlapping one.
    """
    overlapped_anns = getOverlappedAnnotations(annotations)
    #  Create OEs from overlapped Annotations
    overlapped_oes = getOverlappedOntologyElements(overlapped_anns)
    #  Group overlapped OEs by text
    overlapped_by_text = getOverlappedOntologyElementsGroupByText(overlapped_oes)
    sem_concepts = []
    for oe_list in overlapped_by_text:
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

def getOverlappedOntologyElements(self, nested_annotations):
    """
    Creates Ontology Elements according to a given list of overlapped annotations
    :param nested_annotations: A dict of Annotation as given by the getOverlappedAnnotations method
    :return: dict{OntologyElement: list<OntologyElement>}: Key is overlapping OntologyElement,
    value is a list of OntologyElements overlapped by their key
    """
    oelements = {}
    for ann, overlapped_anns in nested_annotations.iteritems():
        oe_list = annotationToOntologyElements(ann)
        for ov_ann in overlapped_anns:
             ov_oe_list = annotationToOntologyElements(ov_ann)
        for oe in oe_list:
            oelements[oe] = ov_oe_list
    return oelements


def annotationToOntologyElements(self, annotation):
    """
    Creates Ontology Elements according to a given annotation
    :param annotation: Annotation instance
    :return: list<OntologyElement> instances
    """
    oe_list = []
    if annotation and annotation.oc_type:
        for ann_type in annotation.oc_type:
            if ann_type == o_c.OTYPE_CLASS:
                oe = OntologyEntityElement()
            elif ann_type == o_c.OTYPE_IND:
                oe = OntologyInstanceElement()
                if 'classUri' in annotation.extra:
                    oe.classUris = annotation.extra['classUri']
                else:
                    import sys
                    print('Orphan instance %s' % annotation.oc_type[ann_type], sys.stderr)
            elif ann_type == o_c.OTYPE_OPROP:
                oe = OntologyObjectPropertyElement()
                if 'domain' in annotation.extra:
                    oe.domain = annotation.extra['domain']
                if 'range' in annotation.extra:
                    oe.range = annotation.extra['range']
            elif ann_type == o_c.OTYPE_DTPROP:
                oe = OntologyDatatypePropertyElement()
                if 'domain' in annotation.extra:
                    oe.domain = annotation.extra['domain']
                if 'range' in annotation.extra:
                    oe.range = annotation.extra['range']
            elif ann_type == o_c.OTYPE_LITERAL:
                oe = OntologyLiteralElement()
            else:
                oe = None
            if oe:
                oe.annotation = annotation
                oe.uri = annotation.oc_type[ann_type]
                oe_list.append(oe)
    return oe_list


def getOverlappedAnnotations(self, annotations):
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
        i += 1
    return overlapped_anns


def getOverlappedOntologyElementsGroupByText(self, oelements):
    """
    Given a dict of overlapped ontology elements, group them up according to their textual representation.
    :param oelements: A dict of overlapped OEs as given by the getOverlappedOntologyElements method
    :return: list<list<OntologyElement>> A list with overlapping OEs (lists of OEs) that have the same
    underlying text. The first element of each sub-list is the overlapping OE.
    """
    overlapped_oe_by_text = []
    for overlapping_oe, overlapped_oes in oelements.iteritems():
        text_overlaps = {}  # Key is text, value is list of overlapping OEs with that text
        oe_text = overlapping_oe.annotation.text
        text_overlaps[oe_text] = [overlapping_oe]
        for overlapped_oe in overlapped_oes:
            overlapped_text = overlapped_oe.annotation.text
            if overlapped_text in text_overlaps:
                text_overlaps[overlapped_text].append(overlapped_oe)
            else:
                text_overlaps[overlapped_text] = [overlapped_oe]
        for text in text_overlaps:
            oes_with_text = text_overlaps[text]
            overlapped_oe_by_text.append(oes_with_text)
    return overlapped_oe_by_text
