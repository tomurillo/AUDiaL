from NLP.model.OE import *
from dialog.model.SuggestionPair import SuggestionPair
from dialog.config import USE_LABELS, LABEL_PROPS, MAX_SUGGESTIONS
from GeneralUtil import beautifyOutputString


class SuggestionFormatter(object):
    """
    Utility methods for transforming Dialog suggestions into JSON for Web display
    """
    def __init__(self, ontology):
        """
        SuggestionFormatter constructor

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
                    key_label = self.findKeyLabel(vote.candidate.OE)
                    json_vote['candidate'] = key_label
                    json_vote['id'] = vote.id
                    json_vote['vote'] = vote.vote
                    json_vote['task'] = vote.candidate.task
                    json_pair['votes'].append(json_vote)
        return json_pair

    def findKeyLabel(self, oe):
        """
        Finds the label to be displayed in the dialogue for a given suggestion (an OC)
        :param oe: OntologyElement instance
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
                for c_uri in oe.classUris:
                    class_labels.extend(self.findLabels(c_uri) if USE_LABELS else c_uri)
                if class_labels:
                    label = "%s (%s)" % (instance_label, ", ".join(class_labels))
                else:
                    label = instance_label
        elif isinstance(oe, OntologyLiteralElement):
            label = uri
        else:
            label = ", ".join(self.findLabels(uri)) if USE_LABELS else uri
        return label

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
                rdf_labels = self.o.graph.objects(URIRef(uri), URIRef(label_prop))
                if rdf_labels:
                    break
        if rdf_labels:
            labels = map(self.o.stripNamespace, rdf_labels)
        else:
            labels.append(beautifyOutputString(self.o.stripNamespace(uri)))
        return labels
