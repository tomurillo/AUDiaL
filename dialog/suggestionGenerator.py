from dialog.model.Vote import *
from NLP.model.OE import *
from NLP.model.SemanticConcept import *
from dialog.config import *
from NLP.NLHandler import synonymsOfWord, similarityBetweenWords, soundexSimilarityBetweenWords
from NLP.constants import *
from NLP.util.TreeUtil import containNodes
from GeneralUtil import beautifyOutputString

class SuggestionGenerator(object):
    """
    Dialogue Suggestions generator
    """

    def __init__(self, ontology, force_parents=True):
        """
        SuggestionGenerator constructor.
        :param ontology: An instantiated ontology
        :param force_parents: whether parent classes/properties should be considered for the suggestions
        :return: None
        """
        self.o = ontology
        self.force_parents = force_parents

    def createVotes(self, key, poc, add_none, skip=None):
        """
        Generate learning votes for the given parameters
        :param key: SuggestionKey instance
        :param poc:
        :param add_none:
        :param skip: list of SemanticConcepts to skip; default None
        :return: list<Vote>
        """
        votes = []
        if skip is None:
            skip = []
        skip_uris = [sc.OE.print_uri() for sc in skip]
        candidates = set()
        for neighbor_sc in key.nearest_neighbors:
            sc_candidates = self.findCandidateElements(neighbor_sc)
            candidates.update(sc_candidates)

        return votes

    def createVotesfromOEs(self, oe_list, skip_uris, poc, text, sc_neighbor=None):
        """
        Generate a vote from suggestion OntologyElements
        :param oe_list: A list of OntologyElement instances
        :param skip_uris: URIs of suggestions not to consider
        :param poc: A POC instance
        :param text: Text from a SuggestionKey
        :param sc_neighbor: SemanticConcept instance
        :return: list<Vote>: votes created from oe_list
        """
        suggestions = []
        for oe in oe_list:
            if oe.print_uri() not in skip_uris:
                oe_uri = oe.uri
                if oe_uri not in suggestions:
                    suggestions.append(oe_uri)
                    if poc.annotation:
                        oe.annotation = poc.annotation
                    if isinstance(oe, OntologyDatatypePropertyElement) and sc_neighbor:
                        oe.governor = sc_neighbor.OE
                    name = self.o.stripNamespace(oe_uri)
                    if not name:
                        name = oe_uri
                    vote = self.createVote(text, name, oe)
                    suggestions.append(vote)
                    suggestions.extend(self.createAdditionalVotes(text, name, oe, poc, added=False))
        return suggestions

    def createVote(self, text, p_name, oe, task=None):
        """
        Creates a new Vote from the given parameters
        :param text: User-input text from a SuggestionKey
        :param p_name: string; formal ontology name (or URI) of an OntologyElement
        :param oe: OntologyElement instance
        :param task: Ontology task
        :return: Vote instance
        """
        vote = Vote()
        human_name = beautifyOutputString(p_name)
        sc = SemanticConcept()
        sc.OE = oe
        sc.task = task
        vote.candidate = sc
        vote.vote = self.computeSimilarityScore(text, human_name)
        return vote

    def createAdditionalVotes(self, text, p_name, oe, poc, added):
        """
        Generates new votes from a given OE to consider common numerical tasks
        :param text: User-input text from a SuggestionKey
        :param p_name: string; formal ontology name (or URI) of an OntologyElement
        :param oe: OntologyElement instance
        :param poc: POC instance
        :param added: Whether the OE has already been added to the suggestions
        :return: List<Vote> additional votes
        """
        suggestions = []
        if QUICK_TASKS and isinstance(oe, OntologyDatatypePropertyElement):
            jj_tags = [JJ_TREE_POS_TAG, JJR_TREE_POS_TAG, JJS_TREE_POS_TAG, VBN_TREE_POS_TAG, RBS_TREE_POS_TAG]
            if containNodes(poc.tree, jj_tags):
                for task in QUICK_TASKS:
                    new_oe = oe.deepcopy()
                    new_oe.added = added
                    vote = self.createVote(text, p_name, new_oe, task)
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
                    candidates.append(self.createOntologyElementforURI(p, 'datatypeProperty'))
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
                candidates.append(self.createOntologyElementforURI(neighbor_uri, 'entity'))
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
            classes = []
            for s, p, _ in literal_oe.triples:
                if self.o.individualExists(s):
                    classes.extend(self.o.getClassOfElement(s, stripns=False))
                elif self.o.classExists(s):
                    classes.append(s)
            for c in classes:
                candidates.extend(self.findCandidatesForClass(c))
        return candidates

    def createOntologyElementforURI(self, uri, oe_type='any'):
        """
        Given an URI creates an appropriate OntologyElement instance
        :param uri: an element's URI (string)
        :param oe_type: the specific OntologyElement subclass to create. 'Any' to infer it automatically
        :return: an OntologyElement instance (N.B. only its uri property is set); None if the URI does not match an
        element of the given type in the ontology or if it does not exist.
        """
        ns = self.o.getNamespace(uri)
        name = self.o.stripNamespace(uri)
        oe = None
        if oe_type in ['class', 'entity', 'any'] and self.o.classExists(name, ns):
            oe = OntologyEntityElement()
        elif oe_type in ['individual', 'instance', 'any'] and self.o.individualExists(name, ns):
            oe = OntologyInstanceElement()
        elif oe_type in ['objectProperty', 'property', 'any'] and self.o.propertyExists(name, 'objectProperty', ns):
            oe = OntologyObjectPropertyElement()
        elif oe_type in ['datatypeProperty', 'property', 'any'] and self.o.propertyExists(name, 'datatypeProperty', ns):
            oe = OntologyDatatypePropertyElement()
        elif oe_type in ['literal', 'value', 'any'] and self.o.individualExists(name, ns):
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