from NLP.model.OE import *
from dialog.model.SuggestionPair import SuggestionPair
from dialog.config import USE_LABELS, LABEL_PROPS, MAX_SUGGESTIONS
from GeneralUtil import beautifyOutputString, replaceLastCommaWithAnd


class OutputFormatter(object):
    """
    Utility methods for transforming Dialog suggestions and answers into JSON for Web display
    """
    def __init__(self, ontology):
        """
        OutputFormatter constructor

        """
        self.o = ontology

    def suggestionPairToJSON(self, pair):
        """
        Convert a SuggestionPair instance to an adapted JSON representation to be displayed in a web form
        :param pair: SuggestionPair instance containing dialogue options to be shown to the user
        :return: dict; JSON object representing the suggestions
        """
        json_pair = {}
        if isinstance(pair, SuggestionPair):
            json_pair['text'] = pair.key.text
            json_pair['votes'] = []
            votes = pair.votes[: MAX_SUGGESTIONS]
            for vote in votes:
                if vote.candidate and vote.candidate.OE:
                    json_vote = {}
                    key_label = self.findOELabel(vote.candidate.OE)
                    json_vote['candidate'] = key_label
                    json_vote['id'] = vote.id
                    json_vote['score'] = vote.vote
                    json_vote['task'] = vote.candidate.task
                    json_pair['votes'].append(json_vote)
        return json_pair

    def findOELabel(self, oe, print_generic=True):
        """
        Finds the label to be displayed for a given OC
        :param oe: OntologyElement instance
        :param print_generic: boolean; whether to print also the labels of the generic resources this OC belongs to,
        such as classes of an instance. Defaults to True.
        :return: string; label for the given OC
        """
        label = ""
        uri = ""
        if isinstance(oe, OntologyElement):
            uri = oe.uri
        if isinstance(oe, OntologyInstanceElement):
            instance_label = ""
            if len(oe.uris) > 1:  # Several instances of same class
                i_labels = []
                for i_uri in oe.uris:
                    i_labels.extend(self.findLabels(i_uri) if USE_LABELS else i_uri)
                if len(i_labels) > 1:
                    instance_label = ", ".join(i_labels)
            if not instance_label:
                instance_label = ", ".join(self.findLabels(uri)) if USE_LABELS else uri
            if instance_label:
                class_labels = []
                if print_generic:
                    for c_uri in oe.classUris:
                        class_labels.extend(self.findLabels(c_uri) if USE_LABELS else c_uri)
                if class_labels:
                    label = "%s (%s)" % (instance_label, ", ".join(class_labels))
                else:
                    label = instance_label
        elif isinstance(oe, OntologyLiteralElement):
            label = self.findVisualizationResourceLabel(oe)
        else:
            label = self.printLabelsOfUri(uri)
        return label

    def printLabelsOfUri(self, uri):
        """
        Return a comma-separated list of labels found for the resource with the given URI
        :param uri: string; a resource's URI
        :return: string; print-ready labels
        """
        labels_str = uri
        if USE_LABELS:
            labels_str = replaceLastCommaWithAnd(", ".join(self.findLabels(uri)))
        return labels_str

    def findLabels(self, uri):
        """
        Return all available labels for the given resource in the ontology. If no label-related properties are found
        falls back to the beautified resource name
        :param uri: string; a resource URI
        :return: list<string>; found labels for the resource
        """
        labels = []
        rdf_labels = self.o.getRDFLabel(uri)
        if not rdf_labels:
            #  Search custom label properties
            from rdflib import URIRef
            for label_prop in LABEL_PROPS:
                rdf_labels = list(self.o.graph.objects(URIRef(uri), URIRef(label_prop)))
                if rdf_labels:
                    break
        if rdf_labels:
            labels = map(self.o.stripNamespace, rdf_labels)
        else:
            labels.append(self.quickURILabel(uri))
        return labels

    def findVisualizationResourceLabel(self, oe):
        """
        Format labels of elements that may belong to the visualization ontology
        :param oe: OntologyLiteralElement instance
        :return: string; label to display
        """
        label = ''
        if isinstance(oe, OntologyLiteralElement):
            from const import VIS_NS
            has_text_prop = '%s#%s' % (VIS_NS, self.o.SytacticDataProperty.HAS_TEXT)
            if oe.triples:
                if oe.triples[0][1] == has_text_prop:
                    role_p = self.o.SyntacticProperty.HAS_SYNTACTIC_ROLE
                    roles = []
                    for triple in oe.triples:
                        roles.extend([r.replace('_SR', '').lower() for r in self.o.getObjects(triple[0], role_p)])
                    label += ' (text of %s in the diagram)' % ', '.join(roles)
                    label = replaceLastCommaWithAnd(label)
        if not label and isinstance(oe, OntologyElement):  # Fallback to name in URI
            label = self.quickURILabel(oe.uri)
        return label

    def quickURILabel(self, uri):
        """
        Create a human-readable label from an URI itself without any further ontology search
        :param uri: string
        :return: string; beautified URI's name
        """
        from const import VIS_NS
        ns = self.o.getNamespace(uri)
        name = self.o.stripNamespace(uri)
        if name:
            if ns == VIS_NS:  # Remove suffixes of the Upper Visualization Ontology
                suffix = name[-3:]
                if suffix in ['_GO', '_SR', '_GR', '_IR']:
                    name = name[:-3]
            label = beautifyOutputString(name)
        else:
            label = "Empty"
        return label
