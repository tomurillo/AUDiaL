from dialog.model.Vote import *
from NLP.model.SemanticConcept import *
from NLP.model.Annotation import *
from NLP.model.POC import *
from dialog.config import *
from NLP.NLHandler import synonymsOfWord, similarityBetweenWords, soundexSimilarityBetweenWords
from NLP.constants import *
from NLP.util.TreeUtil import containNodes
from ontology.upper_vis_ontology import UpperVisOntology
from GeneralUtil import beautifyOutputString


class SuggestionGenerator(object):
    """
    Dialogue Suggestions generator
    """

    def __init__(self, query, ontology, force_parents=True):
        """
        SuggestionGenerator constructor.
        :param query: Consolidated Query instance
        :param ontology: An instantiated ontology
        :param force_parents: whether parent classes/properties should be considered for the suggestions
        :return: None
        """
        self.q = query
        self.o = ontology
        self.force_parents = force_parents

    def createVotes(self, key, poc, add_none, skip=None, add_text_labels=False, skip_non_tasks=False):
        """
        Generate learning votes for the given parameters
        :param key: SuggestionKey instance; contains neighbor OEs and user text
        :param poc: POC instance; user input without a supporting ontology resource
        :param add_none: whether to add None votes to the list
        :param skip: list of SemanticConcepts to skip; default None
        :param add_text_labels: whether add textual labels found in the diagram to the suggestions
        :param skip_non_tasks: whether to skip votes not related to visualization tasks
        :return: list<Vote>: votes generated from the SuggestionKey (neighbor suggested ontology resources) and a POC
        (user input not found in the ontology)
        """
        votes = []
        if skip is None:
            skip = []
        skip_uris = [sc.OE.print_uri() for sc in skip]
        if add_text_labels and not skip_non_tasks:
            votes.extend(self.createTextVotes(key.text))
        votes.extend(self.createTaskVotes(key.text))
        if not skip_non_tasks:
            candidates = set()
            for neighbor_sc in key.nearest_neighbors:
                neighbor_candidates = set()
                sc_candidates = self.findCandidateElements(neighbor_sc)
                candidates.update(sc_candidates)
                neighbor_candidates.update(sc_candidates)
                votes.extend(self.createVotesfromOEs(sc_candidates, poc, key.text, neighbor_sc, skip_uris))
                if neighbor_sc.OE not in neighbor_candidates:
                    votes.extend(self.createAdditionalVotes(key.text, neighbor_sc.OE, poc, added=True))
            left_over_votes_oes = []
            left_over_oes = self.findLeftOverOEs()
            for oe in left_over_oes:
                if oe not in candidates:
                    candidates.add(oe)
                    left_over_votes_oes.append(oe)
            votes.extend(self.createVotesfromOEs(left_over_votes_oes, poc, key.text, None, skip_uris))
        if add_none:
            none_vote = self.createNoneVote(poc)
            votes.append(none_vote)
        return votes

    def createTextVotes(self, key_text, limit=100):
        """
        Create votes from occurrences of the has_text property in the ontology
        :param key_text: text input by the user
        :param limit: maximum number of votes to create (default 100)
        :return: list<Vote>
        """
        votes = {}  # Key: Literal string; value: Vote containing that Literal as candidate
        if key_text and isinstance(self.o, UpperVisOntology):
            from dialog.learning.util import PRIORITY_DIAG_LABELS
            i = 0
            for element, prop, text_literal in self.o.yieldTextElement():
                if text_literal:
                    text = str(text_literal)
                    if text in votes:
                        votes[text].candidate.OE.triples.append((str(element), str(prop), text))
                    else:
                        oe = self.createOntologyElementforURI(text, 'literal', check_exists=False)
                        oe.triples.append((str(element), str(prop), text))
                        v = self.createVote(key_text, oe)
                        if PRIORITY_DIAG_LABELS and v.vote < 1:
                            v.vote += 1
                        votes[text] = v
                        i += 1
                        if i >= limit:
                            break
                else:
                    break
        return votes.values()

    def createTaskVotes(self, key_text):
        """
        Create votes from visualization task instances
        :param key_text: text input by the user
        :return: list<Vote>
        """
        votes = []
        if not self.q.task:  # If task has already been found there is no need to cast task votes
            tasks = self.o.getTaskVerbalizations()
            for t, verbs in tasks.iteritems():
                best_sim = -1
                for v in verbs:
                    sim = self.computeSimilarityScore(key_text, v)
                    if sim > best_sim:
                        best_sim = sim
                vote = Vote()
                t_uri = "%s#%s" % (self.o.VIS_NS, t)
                sc = SemanticConcept()
                sc.OE = self.createOntologyElementforURI(t_uri, 'instance', check_exists=False)
                sc.task = t
                sc.answer = True
                vote.candidate = sc
                vote.vote = best_sim
                votes.append(vote)
        return votes

    def createVotesfromOEs(self, oe_list, poc, text, sc_neighbor=None, skip_uris=None):
        """
        Generate votes from suggestion OntologyElements
        :param oe_list: A list of OntologyElement instances
        :param poc: A POC instance
        :param text: Text from a SuggestionKey
        :param sc_neighbor: SemanticConcept instance
        :param skip_uris: URIs of suggestions not to consider
        :return: list<Vote>: votes created from oe_list
        """
        if skip_uris is None:
            skip_uris = []
        suggestions = []
        votes = []
        for oe in oe_list:
            if isinstance(oe, OntologyElement) and oe.print_uri() not in skip_uris:
                oe_uri = oe.uri
                if oe_uri not in suggestions:
                    suggestions.append(oe_uri)
                    if isinstance(poc, Annotation):
                        oe.annotation = poc
                    else:
                        oe.annotation = Annotation()
                        oe.annotation.populateFromPOC(poc)
                    if isinstance(oe, OntologyDatatypePropertyElement) and sc_neighbor:
                        oe.governor = sc_neighbor.OE
                        oe.range = self.o.rangeOfProperty(oe_uri, stripns=False)
                    vote = self.createVote(text, oe)
                    votes.append(vote)
                    votes.extend(self.createAdditionalVotes(text, oe, poc, added=False))
        return votes

    def createFilterVotes(self, key, filter_instance, focus, add_vis=True, add_none=True):
        """
        Create votes for a query filter
        :param key: SuggestionKey instance
        :param filter_instance: QueryFilter instance
        :param focus: POC instance; focus of the query
        :param add_vis: whether to add and give higher priority to visualization properties
        :param add_none: whether to add None votes to the output
        :return: list<Vote>
        """
        votes = []
        if isinstance(focus, POC):
            vote = self.createFocusVote(focus)
            if vote:
                votes.append(vote)
        if add_vis:
            from dialog.learning.config import PRIORITY_DIAG_LABELS
            from const import VIS_NS
            vis_label_uri = "%s#%s" % (VIS_NS, 'is_labeled_by')
            vis_label_oe = self.createOntologyElementforURI(vis_label_uri, 'datatypeProperty', check_exists=False)
            v = self.createVote(key.text, vis_label_oe)
            if PRIORITY_DIAG_LABELS and v.vote < 1:
                v.vote += 1
            votes.append(v)
        votes.extend(self.createGenericVotes(key, filter_instance.annotation, add_none=False))
        if add_none:
            none_vote = self.createNoneVote(focus)
            votes.append(none_vote)
        return votes

    def createFocusVote(self, poc):
        """
        Create a filter vote for the question's focus (i.e. the answer type)
        :param poc: POC instance; the query's focus
        :return: Vote instance
        """
        v = None
        if isinstance(poc, POC):
            v = Vote()
            if isinstance(poc.head, POC):
                v.candidate = poc.head
            else:
                v.candidate = poc
        return v

    def createGenericVotes(self, key, poc, add_none=True, max=10000, skip=None, add_text_labels=False,
                           skip_non_tasks=False):
        """
        Create potential votes when no neighbor OEs have been found in the user query
        :param key: SuggestionKey instance
        :param poc: POC or Annotation instance
        :param add_none: whether to add None votes to the output
        :param max: int; maximum number of votes to generate
        :param skip: list of SemanticConcepts to skip; default None
        :param add_text_labels: whether to add textual labels found in the diagram to the suggestions
        :param skip_non_tasks: whether to skip votes not related to visualization tasks
        :return: list<Vote>
        """
        votes = []
        n = 0
        if skip is None:
            skip = []
        skip_uris = [sc.OE.print_uri() for sc in skip]
        if add_text_labels and not skip_non_tasks:
            text_votes = self.createTextVotes(key.text)
            votes.extend(text_votes)
            n += len(text_votes)
        if n < max:
            task_votes = self.createTaskVotes(key.text)
            votes.extend(task_votes)
            n += len(task_votes)
        if n < max and not skip_non_tasks:
            oes = self.findGenericOEs(max, skip_uris)
            for oe in oes:
                if isinstance(poc, Annotation):
                    oe.annotation = poc
                else:
                    oe.annotation = Annotation()
                    oe.annotation.populateFromPOC(poc)
                vote = self.createVote(key.text, oe)
                votes.append(vote)
                n += 1
                n_left = max - n
                if n_left > 0:
                    all_additional_votes = self.createAdditionalVotes(key.text, oe, poc, added=False)
                    additional_votes = all_additional_votes[:n_left]
                    votes.extend(additional_votes)
                    n += len(additional_votes)
                    if n >= max:
                        break
        if n < max and not skip_non_tasks:
            n_left = max - n
            all_leftover_votes = self.createVotesfromOEs(self.findLeftOverOEs(), poc, key.text, None, skip_uris)
            leftover_votes = all_leftover_votes[:n_left]
            n += len(leftover_votes)
            votes.extend(leftover_votes)
        if add_none:
            none_vote = self.createNoneVote(poc)
            votes.append(none_vote)
        return votes

    def findGenericOEs(self, max_elems, skip_uris=None):
        """
        Find top-most ontology resources (entities and properties) and return them as OntologyElement instances
        :param max_elems: int; maximum number of elements to return
        :param skip_uris: list<string>; URIs of OntologyElements not to consider
        :return: list<OntologyElement>
        """
        if skip_uris is None:
            skip_uris = []
        n = 0
        oes = []
        for p_uri, p_type in self.o.yieldResource(res_type='property'):
            if p_uri not in skip_uris and not self.o.getParentProperties(p_uri, ns=None, stripns=False):
                n += 1
                oes.append(self.createOntologyElementforURI(p_uri, p_type, check_exists=False))
                if n >= max_elems:
                    break
        if n < max_elems:
            for c_uri, _ in self.o.yieldResource(res_type='class'):
                if c_uri not in skip_uris and not self.o.getParentClasses(c_uri, ns=None, stripns=False):
                    n += 1
                    oes.append(self.createOntologyElementforURI(c_uri, "class", check_exists=False))
                    if n >= max_elems:
                        break
        return oes

    def createVote(self, text, oe, task=None):
        """
        Creates a new Vote from the given parameters
        :param text: User-input text from a SuggestionKey
        :param oe: OntologyElement instance
        :param task: Ontology task
        :return: Vote instance
        """
        vote = None
        if isinstance(oe, OntologyElement):
            vote = Vote()
            name = self.o.stripNamespace(oe.uri)
            if not name:
                name = oe.uri
            human_name = beautifyOutputString(name)
            sc = SemanticConcept()
            sc.OE = oe.deepcopy()
            sc.task = task
            vote.candidate = sc
            vote.vote = self.computeSimilarityScore(text, human_name)
        return vote

    def createNoneVote(self, poc=None):
        """
        Creates a lowest-priority Vote for an empty option
        :param poc: POC instance (optional)
        :return: Vote instance
        """
        vote = Vote()
        oe = OntologyNoneElement()
        if isinstance(poc, POC):
            oe.annotation = Annotation()
            oe.annotation.populateFromPOC(poc)
        elif isinstance(poc, Annotation):
            oe.annotation = poc
        sc = SemanticConcept()
        sc.OE = oe
        vote.candidate = sc
        vote.vote = -1.0
        return vote

    def createAdditionalVotes(self, text, oe, poc, added):
        """
        Generates new votes from a given OE to consider common numerical tasks
        :param text: User-input text from a SuggestionKey
        :param oe: OntologyElement instance
        :param poc: POC instance
        :param added: Whether the OE has already been added to the suggestions
        :return: List<Vote> additional votes
        """
        suggestions = []
        if QUICK_TASKS and isinstance(oe, OntologyDatatypePropertyElement):
            jj_tags = [JJ_TREE_POS_TAG, JJR_TREE_POS_TAG, JJS_TREE_POS_TAG, VBN_TREE_POS_TAG, RBS_TREE_POS_TAG]
            if isinstance(poc, POC) and containNodes(poc.tree, jj_tags):
                for task in QUICK_TASKS:
                    new_oe = oe.deepcopy()
                    new_oe.added = added
                    vote = self.createVote(text, new_oe, task)
                    suggestions.append(vote)
        return suggestions

    def findCandidateElements(self, sc):
        """
        Searches in the ontology for candidate OEs for a clarification dialogue given a Semantic Concept
        :param sc: SemanticConcept instance
        :return: list<OntologyElement>: list of candidate OEs to be presented to the user
        """
        candidates = []
        oe = sc.OE
        if oe:
            class_uris = []
            if isinstance(oe, OntologyInstanceElement):
                class_uris.extend(oe.classUris)
            elif isinstance(oe, OntologyEntityElement):
                class_uris.append(oe.uri)
            elif isinstance(oe, OntologyLiteralElement):
                prop_uris = self.findCandidatesForLiteral(oe)
                for p in prop_uris:
                    candidates.append(self.createOntologyElementforURI(p, 'objectProperty'))
            elif isinstance(oe, (OntologyObjectPropertyElement, OntologyDatatypePropertyElement)):
                candidates.extend(self.findCandidatesForProperty(oe))
            neighbor_classes = set()
            for uri in class_uris:
                candidate_uris = self.findCandidatesForClass(uri)
                for prop_uri in candidate_uris:
                    candidates.append(self.createOntologyElementforURI(prop_uri, 'property'))
                to_consider = [uri]
                if self.force_parents:
                    to_consider.extend(self.o.getParentClasses(uri, ns=None, stripns=False))
                for c_uri in to_consider:
                    neighbor_classes.update(self.o.neighborRangeOrDomainClasses(c_uri, 'domain', stripns=False))
                    neighbor_classes.update(self.o.neighborRangeOrDomainClasses(c_uri, 'range', stripns=False))
            for neighbor_uri in neighbor_classes:
                oe_candidate = self.createOntologyElementforURI(neighbor_uri, 'entity')
                if oe_candidate:
                    candidates.append(oe_candidate)
        return list(set(candidates))

    def findCandidatesForClass(self, class_uri):
        """
        Searches for candidates for the given class (properties where the class belongs to their domain or range)
        :param class_uri: string; a Class URI
        :return: list<string>: candidate property URIs
        """
        candidates = []
        classes = [class_uri]
        if self.force_parents:
            classes.extend(self.o.getParentClasses(class_uri, ns=None, stripns=False))
        for c in classes:
            candidates.extend(self.o.propertiesWithRangeOrDomain(c, 'range', stripns=False))
            candidates.extend(self.o.propertiesWithRangeOrDomain(c, 'domain', stripns=False))
        return list(set(candidates))

    def findCandidatesForProperty(self, prop_oe):
        """
        Find candidate suggestions for the given property: properties having the same range or domain; and neighbor
        classes of the classes of its range and domain
        :param prop_oe: OntologyObjectPropertyElement or OntologyDatatypePropertyElement instance
        :return: list<OntologyElement>: list of candidate OEs
        """
        candidates = []
        if isinstance(prop_oe, (OntologyObjectPropertyElement, OntologyDatatypePropertyElement)):
            classes = []
            classes_parents = []
            classes_neighbor = []
            properties = []
            classes.extend(self.o.rangeOfProperty(prop_oe.uri, stripns=False))
            classes.extend(self.o.domainOfProperty(prop_oe.uri, stripns=False))
            if self.force_parents:
                for c in classes:
                    classes_parents.extend(self.o.getParentClasses(c, ns=None, stripns=False))
            classes.extend(classes_parents)
            if len(classes) <= 1 and FORCE_SUGGESTIONS:
                classes.extend(self.o.getClasses(self.o.getNamespace(prop_oe.uri)))
            for class_uri in classes:
                properties.extend(self.o.propertiesWithRangeOrDomain(class_uri, 'domain', stripns=False))
                properties.extend(self.o.propertiesWithRangeOrDomain(class_uri, 'range', stripns=False))
                classes_neighbor.extend(self.o.neighborRangeOrDomainClasses(class_uri, 'domain', stripns=False))
                classes_neighbor.extend(self.o.neighborRangeOrDomainClasses(class_uri, 'range', stripns=False))
            if FORCE_SUGGESTIONS:
                properties.extend(self.o.getProperties(prop_type='all', ns=self.o.getNamespace(prop_oe.uri)))
            for p in properties:
                candidates.append(self.createOntologyElementforURI(p, 'property'))
            for c in classes_neighbor:
                candidates.append(self.createOntologyElementforURI(c, 'entity'))
        return candidates

    def findCandidatesForLiteral(self, literal_oe):
        """
        Find candidate suggestions for the given Literal (candidates of the classes having the Literal as the value
        for one of their datatype properties)
        :param literal_oe: OntologyLiteralElement instance
        :return: list<string>; candidate property URIs
        """
        candidates = []
        if isinstance(literal_oe, OntologyLiteralElement) and literal_oe.triples:
            classes = set()
            for s, p, _ in literal_oe.triples:
                if self.o.individualExists(s):
                    classes.update(self.o.getClassOfElement(s, stripns=False))
                elif self.o.classExists(s):
                    classes.update(s)
            for c in classes:
                candidates.extend(self.findCandidatesForClass(c))
        return candidates

    def findLeftOverOEs(self):
        """
        Returns properties without range and domain (or generic range and domains) and generic ontology resources; this
        are left over elements since they have not been considered anywhere else in the generation of suggestions.
        :return: List<OntologyElement> Leftover OntologyElements
        """
        from rdflib import RDF, RDFS, OWL  # Namespaces
        #  Generic resources
        p_label = self.createOntologyElementforURI(RDFS.label, 'datatypeProperty', check_exists=False)
        p_type = self.createOntologyElementforURI(RDF.type, 'objectProperty', check_exists=False)
        c_thing = self.createOntologyElementforURI(OWL.thing, 'entity', check_exists=False)
        elements = [p_label, p_type, c_thing]
        #  Datatype properties without domain
        dps_no_domain = self.o.propertiesWithoutRangeOrDomain('datatype', 'domain', stripns=False)
        elements.extend(self.createOntologyElementforURI(uri, 'datatypeProperty', False) for uri in dps_no_domain)
        #  Properties having owl:Thing as their domain or range
        general_dom_ps = self.o.propertiesWithRangeOrDomain(OWL.thing, 'domain', stripns=False)
        if self.force_parents:
            general_dom_ps_parents = [self.o.getParentProperties(uri, ns=None, stripns=False) for uri in general_dom_ps]
            general_dom_ps.extend(general_dom_ps_parents)
        elements.extend(self.createOntologyElementforURI(uri, 'property', False) for uri in general_dom_ps)
        general_ran_ps = self.o.propertiesWithRangeOrDomain(OWL.thing, 'range', stripns=False)
        if self.force_parents:
            general_ran_ps_parents = [self.o.getParentProperties(uri, ns=None, stripns=False) for uri in general_ran_ps]
            general_ran_ps.extend(general_ran_ps_parents)
        elements.extend(self.createOntologyElementforURI(uri, 'property') for uri in general_ran_ps)
        #  Instances of owl:Thing
        things = self.o.getInstances(OWL.thing, stripns=False)
        elements.extend(self.createOntologyElementforURI(uri, 'individual', check_exists=False) for uri in things)
        return elements

    def createOntologyElementforURI(self, uri, oe_type='any', check_exists=True):
        """
        Given an URI creates an appropriate OntologyElement instance
        :param uri: an element's URI (string)
        :param oe_type: the specific OntologyElement subclass to create. 'Any' to infer it automatically
        :param check_exists: boolean; whether to check if the element exists in the ontology before creating it
        :return: an OntologyElement instance (N.B. only its uri property is set); None if the URI does not match an
        element of the given type in the ontology or if it does not exist.
        """
        ns = self.o.getNamespace(uri)
        name = self.o.stripNamespace(uri)
        oe = None
        if oe_type in ['class', 'entity', 'any'] and (not check_exists or self.o.classExists(name, ns)):
            oe = OntologyEntityElement()
        elif oe_type in ['individual', 'instance', 'any'] and (not check_exists or self.o.individualExists(name, ns)):
            oe = OntologyInstanceElement()
            oe.uris = [uri]
        elif oe_type in ['objectProperty', 'property', 'any'] and \
                (not check_exists or self.o.propertyExists(name, 'objectProperty', ns)):
            oe = OntologyObjectPropertyElement()
        elif oe_type in ['datatypeProperty', 'property', 'any'] and \
                (not check_exists or self.o.propertyExists(name, 'datatypeProperty', ns)):
            oe = OntologyDatatypePropertyElement()
        elif oe_type in ['literal', 'value', 'any'] and (not check_exists or self.o.individualExists(name, ns)):
            oe = OntologyLiteralElement()
        if oe:
            oe.uri = uri
        return oe

    @staticmethod
    def computeSimilarityScore(text_one, text_two, with_synoynms=3):
        """
        Returns the similarity score between the two given strings
        :param text_one: string
        :param text_two: string
        :param with_synoynms: int; how many synonyms from each input string to consider for final score computation
        :return: float; similarity score between text_one and text_two
        """
        from textdistance import monge_elkan
        sim_main = similarityBetweenWords(text_one, text_two, monge_elkan)  # Main similarity between the words
        #  Similarity measures between each word and the other one's synonyms
        synonyms_one = synonymsOfWord(text_one, pos_tag=None, n_synonyms=with_synoynms)
        synonyms_two = synonymsOfWord(text_two, pos_tag=None, n_synonyms=with_synoynms)
        simsyn_one = 0.0
        if synonyms_one:
            for syn in synonyms_one:
                simsyn_one += similarityBetweenWords(syn, text_two, monge_elkan)
            simsyn_one /= len(synonyms_one)
        simsyn_two = 0.0
        if synonyms_two:
            for syn in synonyms_two:
                simsyn_two += similarityBetweenWords(syn, text_one, monge_elkan)
            simsyn_two /= len(synonyms_two)
        soundex_sim = soundexSimilarityBetweenWords(text_one, text_two)  # Phonetic similarity between the words
        w_main = VOTE_CRITERIA_WEIGHTS[0]
        w_sound = VOTE_CRITERIA_WEIGHTS[1]
        w_syn = VOTE_CRITERIA_WEIGHTS[2] / 2.0
        sim_final = w_main * sim_main + w_sound * soundex_sim + w_syn * simsyn_one + w_syn * simsyn_two
        return sim_final
