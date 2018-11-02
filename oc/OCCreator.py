class OCCreator(object):
    """
    Ontology Concept Creator
    """
    def getOverlappedAnnotations(self, annotations):
        """
        Returns which annotations are overlapped by other annotations
        :param annotations: a list of Annotation instances
        :return: dict{Annotation: list<Annotation>}: Key is overlapping Annotation, value is a list of Annotation that
        are overlapped by the key
        """
        # TODO continue here
