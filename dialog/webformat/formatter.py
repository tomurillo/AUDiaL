from NLP.model.SemanticConcept import *
from dialog.model.SuggestionPair import SuggestionPair
from dialog.config import USE_LABELS, LABEL_PROPS, MAX_SUGGESTIONS
from GeneralUtil import beautifyOutputString, replaceLastCommaWithAnd

class OutputFormatter(object):
    """
    Utility methods for transforming Dialog suggestions and answers into JSON for Web display
    """
    def __init__(self, ontology, skip_inflect=False):
        """
        OutputFormatter constructor
        :param ontology: A loaded ontology instance
        :param skip_inflect: boolean; Whether to skip loading the inflect object (used to generate NL output)
        """
        self.o = ontology
        self.p = None  # Inflect instance for proper pluralization and conjugation of output words
        if not skip_inflect:
            import inflect
            self.p = inflect.engine()

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
            if len(pair.votes) > MAX_SUGGESTIONS:
                for v in pair.votes:
                    if isinstance(v.candidate, SemanticConcept) and isinstance(v.candidate.OE, OntologyNoneElement):
                        if v not in votes:
                            votes.append(v)  # Append NoneVote
                        break
            for vote in votes:
                if vote.candidate and vote.candidate.OE:
                    json_vote = {}
                    key_label = self.findOELabel(vote.candidate.OE)
                    json_vote['candidate'] = key_label
                    json_vote['id'] = vote.id
                    json_vote['score'] = "%.2f" % vote.vote
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
        elif isinstance(oe, OntologyNoneElement):
            label = "Not related to any of the suggestions"
        else:
            label = self.printLabelsOfUri(uri)
        return label

    def printLabelsOfUri(self, uri, res_type=None):
        """
        Return a comma-separated list of labels found for the resource with the given URI
        :param uri: string; a resource's URI
        :param res_type: string; the resource type: 'instance', 'class', 'datatypeProperty', 'objectProperty',
        or 'literal'. None if not relevant or unknown.
        :return: string; print-ready labels
        """
        labels_str = uri
        if USE_LABELS:
            labels_str = replaceLastCommaWithAnd(", ".join(self.findLabels(uri, res_type)))
        return labels_str

    def findLabels(self, uri, res_type=None):
        """
        Return all available labels for the given resource in the ontology. If no label-related properties are found
        falls back to the beautified resource name
        :param uri: string; a resource URI
        :param res_type: string; the resource type: 'instance', 'class', 'datatypeProperty', 'objectProperty',
        or 'literal'. None if not relevant or unknown.
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
            labels.append(self.quickURILabel(uri, res_type))
        return labels

    def findVisualizationResourceLabel(self, oe):
        """
        Format labels of elements that may belong to the visualization ontology
        :param oe: OntologyLiteralElement instance
        :return: string; label to display
        """
        label = self.quickURILabel(oe.uri)
        if isinstance(oe, OntologyLiteralElement):
            from const import VIS_NS
            has_text_prop = '%s#%s' % (VIS_NS, self.o.SytacticDataProperty.HAS_TEXT)
            if oe.triples:
                if oe.triples[0][1] == has_text_prop:
                    role_p = self.o.SyntacticProperty.HAS_SYNTACTIC_ROLE
                    roles = []
                    for triple in oe.triples:
                        roles.extend([r.replace('_SR', '').lower() for r in self.o.getObjects(triple[0], role_p)])
                    label += ' (text of %s in the diagram)' % ', '.join(set(roles))
                    label = replaceLastCommaWithAnd(label)
        return label

    def fullLabelForResource(self, uri, oe):
        """
        Return the label for a resource plus extra information according to its type
        :param: The resource URI currently being considered
        :param: OntologyElement instance containing semantic information about the resource
        :return: HTML string
        """
        final_label = ''
        if uri and isinstance(oe, OntologyElement):
            from const import COMMON_NS
            from dialog.config import MAX_EXTRA_INFO
            if isinstance(oe, OntologyObjectPropertyElement):
                p_type = 'objectProperty'
            elif isinstance(oe, OntologyDatatypePropertyElement):
                p_type = 'datatypeProperty'
            else:
                p_type = None
            full_label = ''
            simple_label = self.quickURILabel(uri, p_type)
            generator = None
            i = 0
            if isinstance(oe, OntologyInstanceElement):
                generator = self.o.graph.predicate_objects(uri)
            elif isinstance(oe, (OntologyObjectPropertyElement, OntologyDatatypePropertyElement)):
                generator = self.o.graph.subject_objects(uri)
            elif isinstance(oe, OntologyEntityElement):
                generator = self.o.generateInstances(uri, stripns=False)
            if generator:
                list_markup = "<ol>"
                for thing in generator:
                    item_label = ''
                    if isinstance(oe, OntologyInstanceElement):
                        prop, obj = thing[0], thing[1]
                        if self.o.getNamespace(prop) not in COMMON_NS:
                            l_prop = self.printLabelsOfUri(prop, 'property')
                            l_obj = self.printLabelsOfUri(obj)
                            item_label = "%s %s %s" % (simple_label, l_prop, l_obj)
                    elif isinstance(oe, (OntologyObjectPropertyElement, OntologyDatatypePropertyElement)):
                        subj, obj = thing[0], thing[1]
                        l_subj = self.printLabelsOfUri(subj)
                        l_obj = self.printLabelsOfUri(obj)
                        item_label = "%s %s %s" % (l_subj, simple_label, l_obj)
                    elif isinstance(oe, OntologyEntityElement):
                        item_label = self.printLabelsOfUri(thing)
                    if item_label:
                        list_markup += "<li>%s</li>" % item_label
                        i += 1
                        if i == MAX_EXTRA_INFO:
                            break
                list_markup += "</ol>"
                if isinstance(oe, OntologyEntityElement):
                    full_label = "There %s %s" % (self.p.plural_verb("is", i), self.p.no(simple_label, i).lower())
            if not full_label:
                full_label = self.findOELabel(oe)
            if i > 0:
                final_label = "<h5>%s</h5><section>%s</section>" % (full_label, list_markup)
            else:
                final_label = full_label
        return final_label

    def quickURILabel(self, uri, res_type=None):
        """
        Create a human-readable label from an URI itself without any further ontology search
        :param uri: string
        :param res_type: string; the resource type: 'instance', 'class', 'datatypeProperty', 'objectProperty',
        or 'literal'. None if not relevant or unknown.
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
                if res_type in ['datatypeProperty']:
                    first_chars = name[:4]
                    if first_chars == 'has_':
                        prop_obj = self.p.an(name[4:].replace('_', ' '))
                        name = "has %s of" % prop_obj
            label = beautifyOutputString(name)
        else:
            label = "Empty"
        return label
