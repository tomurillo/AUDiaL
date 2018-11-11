import Ontovis.constants as o_c
from NLP.model.OE import *

class OCCreator(object):
    """
    Ontology Concept Creator
    """

    def getSemanticConcepts(self, annotations):
        """
        Converts annotations to semantic concepts
        :param annotations: An offset-sorted list of Annotation
        :return:
        """
        overlapped_anns = self.getOverlappedAnnotations(annotations)
        overlapped_oes = self.getOverlappedOntologyElements(overlapped_anns)


    def getOverlappedOntologyElements(self, nested_annotations):
        """
        Creates Ontology Elements according to a given list of overlapped annotations
        :param nested_annotations: A dict of Annotation as given by the getOverlappedAnnotations method
        :return: dict{OntologyElement: list<OntologyElement>}: Key is overlapping OntologyElement,
        value is a list of OntologyElements overlapped by their key
        """
        oelements = {}
        for ann, overlapped_anns in nested_annotations.iteritems():
            oe_list = self.annotationToOntologyElements(ann)
            for ov_ann in overlapped_anns:
                    ov_oe_list = self.annotationToOntologyElements(ov_ann)
            for oe in oe_list:
                oelements[oe] = []
                for ov_oe in ov_oe_list:
                    oelements[oe].append(ov_oe)
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
                if overlapping and overlapped:
                    if overlapping not in overlapped_anns:
                        overlapped_anns[overlapping] = []
                    overlapped_anns[overlapping].append(overlapped)
            i += 1
        return overlapped_anns
