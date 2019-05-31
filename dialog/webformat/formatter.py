from NLP.model.QueryFilter import QueryFilterCardinal
from NLP.model.POC import POC
from NLP.model.OE import *
from NLP.model.SemanticConcept import SemanticConcept
from dialog.model.SuggestionPair import SuggestionPair
from dialog.config import USE_LABELS, LABEL_PROPS, MAX_SUGGESTIONS
from GeneralUtil import beautifyOutputString, replaceLastCommaWithAnd
from ontology.bar_chart_ontology import BarChartOntology


class OutputFormatter(object):
    """
    Utility methods for transforming Dialog suggestions and answers for their display to the user
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
            if pair.filter:
                filter_task = self.operatorLabel(pair.filter.operands, pair.filter.op)
            for vote in votes:
                if vote.candidate:
                    json_vote = {}
                    key_label = ''
                    task = None
                    if pair.filter:
                        add_task = True
                        if isinstance(vote.candidate, POC):
                            key_label = self.createFocusLabel(vote.candidate, pair.filter)
                        else:
                            key_label = self.createFilterLabel(vote.candidate, pair.filter)
                            if isinstance(vote.candidate.OE, OntologyNoneElement):
                                add_task = False
                        if add_task:
                            task = filter_task
                    elif isinstance(vote.candidate, SemanticConcept):
                        key_label = self.findOELabel(vote.candidate.OE)
                        task = self.findTaskLabel(vote.candidate.task)
                    json_vote['candidate'] = key_label
                    json_vote['id'] = vote.id
                    json_vote['score'] = "%.2f" % vote.vote
                    json_vote['task'] = task
                    json_pair['votes'].append(json_vote)
        return json_pair

    def createFocusLabel(self, poc, q_filter):
        """
        Create a label to be displayed for the question's focus
        :param poc: POC containing the focus or its head
        :param q_filter: QueryFilter instance being resolved
        :return: string; label of the focus
        """
        if isinstance(q_filter, QueryFilterCardinal):
            units = ''
            if isinstance(self.o, BarChartOntology):
                units = self.o.getChartMeasurementUnit()
            if not units:
                units = poc.rawText
            label = "Query result: '%s'" % units
        else:
            label = poc.rawText
        return label

    def createFilterLabel(self, prop_oc, q_filter):
        """
        Create a label to de displayed for a query filter that may be applied to a property
        :param prop_oc: SemanticConcept instance of the property
        :param q_filter: QueryFilter instance being resolved
        :return: string; label to be displayed in disambiguation dialogue
        """
        label = '(not found)'
        if isinstance(q_filter, QueryFilterCardinal) and isinstance(prop_oc, SemanticConcept):
            oc = prop_oc.OE
            if isinstance(oc, OntologyDatatypePropertyElement):
                from const import VIS_NS
                vis_label_uri = "%s#%s" % (VIS_NS, 'is_labeled_by')
                if oc.uri == vis_label_uri:
                    label = "Diagram Labels"
                else:
                    label = self.findOELabel(oc)
            else:
                label = self.findOELabel(oc)
        return label

    def operatorLabel(self, operand, operator):
        """
        Converts a QueryFilterCardinal task to a NL label
        :param operand: list<string>; numbers or literals to compare against
        :param operator: string; one of QueryFilterCardinal.CardinalFilter
        :return: string; NL representation of the operator
        """
        label = 'return those'
        if operator == QueryFilterCardinal.CardinalFilter.EQ:
            op_label = 'equal to'
        elif operator == QueryFilterCardinal.CardinalFilter.NEQ:
            op_label = 'not equal to'
        elif operator == QueryFilterCardinal.CardinalFilter.GT:
            op_label = 'greater than'
        elif operator == QueryFilterCardinal.CardinalFilter.LT:
            op_label = 'less than'
        elif operator == QueryFilterCardinal.CardinalFilter.GEQ:
            op_label = 'at least'
        elif operator == QueryFilterCardinal.CardinalFilter.LEQ:
            op_label = 'at most'
        else:
            op_label = 'equal'
        label += " %s" % op_label
        label += " %s" % ', '.join(operand)
        return label

    def findTaskLabel(self, task):
        """
        Returns a label to be displayed for an analytic task
        :param task: string; a task URI or a quick task string (such as 'max', 'min', 'sum', 'avg')
        :return: string; label to be shown in dialogue
        """
        from dialog.config import QUICK_TASKS
        label = ''
        if task in QUICK_TASKS:
            label = QUICK_TASKS[task]
        elif task and task[-5:] == '_Task':  # Task is visualization task ontology resource URI
            label = self.quickURILabel(task[:-5])
        return label

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
                    if self.o.getNamespace(uri) == self.o.VIS_NS and uri[-5:] == "_Task":
                        #  Instance is analytical task to be performed on query result
                        label = "Apply task to result"
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
                elif name[-5:] == '_Task':
                    name = name[:-5]
                elif res_type == 'datatypeProperty':
                    first_chars = name[:4]
                    if first_chars == 'has_':
                        prop_obj = self.p.an(name[4:].replace('_', ' '))
                        name = "has %s of" % prop_obj
            label = beautifyOutputString(name)
        else:
            label = "Empty"
        return label
