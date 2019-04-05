from dialog.model.modelUtil import *
from dialog.learning.util import *
from dialog.config import *
from dialog.suggestionGenerator import SuggestionGenerator
from oc.OCUtil import *
from NLP.model.POC import *
from NLP.model.QueryFilter import *


class DialogHandler(object):
    """
    User/system dialog (disambiguation and mapping) utility class
    """

    def __init__(self, query, o):
        """
        DialogHandler constructor.
        :param query: A pre-consolidated Query instance
        :param o: Ontology instance
        :return:
        """
        self.q = query
        self.o = o

    def generateDialogs(self):
        """
        Checks whether it is necessary to generate disambiguation and mapping dialogs; if so, creates them
        :return: SuggestionPair instance if a dialogue is necessary; None otherwise (question can be resolved)
        """
        pair = None
        if self.disambiguationRequired():  # Give priority to disambiguation between OCs
            pair = self.generateDisambiguationDialog()
        elif self.mappingRequired():
            pair = self.generateMappingDialog()
        elif self.filterClarificationRequired():  # Any unresolved filters left?
            pair = self.generateFilterClarificationDialog()
        if pair is False:
            pair = self.generateDialogs()  # Vote was automatically casted; no user action needed
        return pair

    def generateFilterClarificationDialog(self):
        """
        Generates a user dialog to add the focus to a query's filter
        :return: SuggestionPair instance
        """
        key = SuggestionKey()
        pair = SuggestionPair()
        next_filter = nextFilter(self.q)
        key.text = next_filter.annotation.rawText
        pair.key = key
        pair.filter = next_filter
        learning_keys = self.generateLearningKeys(key)
        sug_generator = SuggestionGenerator(self.o, force_parents=True)
        votes = sug_generator.createFilterVotes(key, next_filter, self.q.focus, add_none=True)
        learning_votes = self.loadLearningVotes(learning_keys)
        if learning_votes:
            pair.votes = updateVotesFromLearningVotes(learning_votes, votes)
        else:
            pair.votes = votes
            if LEARNING_ENABLED:
                l_model = {}
                learning_votes = getLearningVotesfromVotes(votes)
                for lkey in learning_keys:
                    l_model[lkey] = learning_votes
                saveLearningModel(l_model)
        if pair.votes:
            return pair
        else:
            return False

    def generateDisambiguationDialog(self):
        """
        Generates a user dialog to disambiguate between ambiguous OCs in the query
        :return: SuggestionPair instance
        """
        key = SuggestionKey()
        pair = SuggestionPair()
        next_ocs = nextAmbiguousOCs(self.q)  # OCs (SemanticConcept instances) closest to question focus
        sc_first = None
        if next_ocs:
            sc_first = next_ocs[0]
            key.text = sc_first.OE.annotation.rawText
        neighbor_ocs = findNearestOCsInQuery(self.q, next_ocs)
        key.nearest_neighbors = neighbor_ocs
        pair.key = key
        #  Search for learning keys in the Ontology and learning votes in the model
        learning_keys = self.generateLearningKeys(key)
        learning_votes = self.loadLearningVotes(learning_keys)
        #  Initialize suggestion pair votes from ambiguous OCs
        suggestion_votes = self.generateInitialVotes(next_ocs)
        if FORCE_DIALOG and sc_first:
            #  Find additional votes by creating a new POC from the OE
            sug_generator = SuggestionGenerator(self.o, force_parents=True)
            poc = POC()
            poc.populateFromAnnotation(sc_first.OE.annotation.copy())
            poc_votes = []
            if neighbor_ocs:
                poc_votes.extend(sug_generator.createVotes(key, poc, add_none=False, skip=next_ocs))
            else:
                poc_votes.extend(sug_generator.createGenericVotes(key, poc, add_none=False, skip=next_ocs))
            candidate_oes = []
            for poc_vote in poc_votes:
                if poc_vote.candidate not in next_ocs and not isinstance(poc_vote.candidate.OE, OntologyNoneElement):
                    poc_vote.candidate.score = poc_vote.vote
                    candidate_oes.append(poc_vote.candidate)
            suggestion_votes.extend(self.generateInitialVotes(candidate_oes))
        if learning_votes:
            pair.votes = updateVotesFromLearningVotes(learning_votes, suggestion_votes)
        else:
            pair.votes = suggestion_votes
            if LEARNING_ENABLED:
                l_model = {}
                learning_votes = getLearningVotesfromVotes(suggestion_votes)
                for lkey in learning_keys:
                    l_model[lkey] = learning_votes
                saveLearningModel(l_model)
        self.resolveOCwithVotesAutomatically(pair)
        if pair.votes:
            return pair
        else:
            return False

    def resolveOCwithVotesAutomatically(self, pair):
        """
        Check available scores of disambiguation vote; if the difference is big enough, automatically cast vote
        :param pair: A SuggestionPair instance with candidate votes
        :return: None; Updates the SuggestionPair instance; votes are empty if they have been automatically resolved
        """
        if len(pair.votes) > 1:
            pair.votes.sort(key=lambda v: v.vote, reverse=True)  # Sort votes descending according to score
            if pair.votes[0].vote - pair.votes[1].vote >= MIN_VOTE_DIFF_RESOLVE:
                from consolidator.Consolidator import Consolidator
                consolidator = Consolidator(self.q)
                self.q = consolidator.disambiguateOCs([pair.votes[0].candidate])
                pair.votes = []

    def generateMappingDialog(self):
        """
        Generates a dialog to map unresolved POCs in the user query to ontology resources (OCs)
        :return: SuggestionPair instance
        """
        pair = SuggestionPair()
        key = SuggestionKey()
        poc = nextPOC(self.q)
        neighbor_ocs = findNearestOCsOfPOC(self.q, poc)
        key.text = poc.rawText
        key.nearest_neighbors = neighbor_ocs
        pair.key = key
        pair.subject = poc
        learning_keys = self.generateLearningKeys(key)
        sug_generator = SuggestionGenerator(self.o, force_parents=True)
        if neighbor_ocs:
            votes = sug_generator.createVotes(key, poc, add_none=True, add_text_labels=True)
        else:
            votes = sug_generator.createGenericVotes(key, poc, add_none=True, add_text_labels=True)
        learning_votes = self.loadLearningVotes(learning_keys)
        if learning_votes:
            pair.votes = updateVotesFromLearningVotes(learning_votes, votes)
        else:
            pair.votes = votes
            if LEARNING_ENABLED:
                l_model = {}
                learning_votes = getLearningVotesfromVotes(votes)
                for lkey in learning_keys:
                    l_model[lkey] = learning_votes
                saveLearningModel(l_model)
        self.resolvePOCwithVotesAutomatically(pair)
        if pair.votes:
            return pair
        else:
            return False

    def resolvePOCwithVotesAutomatically(self, pair):
        """
        Check available scores of mapping votes; if the difference is big enough, automatically cast vote
        :param pair: A SuggestionPair instance with candidate votes
        :return: None; Updates the SuggestionPair instance; votes are empty if they have been automatically resolved
        """
        if len(pair.votes) > 1:
            pair.votes.sort(key=lambda v: v.vote, reverse=True)  # Sort votes descending according to score
            if pair.votes[0].vote - pair.votes[1].vote >= MIN_VOTE_DIFF_RESOLVE:
                from consolidator.Consolidator import Consolidator
                consolidator = Consolidator(self.q)
                self.q = consolidator.resolvePOCtoOC(pair.subject, [pair.votes[0].candidate])
                pair.votes = []

    def generateLearningKeys(self, sugkey):
        """
        Creates a new list of Key for learning from a SuggestionKey
        :param sugkey: SuggestionKey instance
        :param o: Ontology instance
        :return: list<Key>
        """
        key_list = []
        if sugkey and isinstance(sugkey, SuggestionKey):
            if sugkey.nearest_neighbors:
                for sc in sugkey.nearest_neighbors:
                    lk = Key()  # Learning Key
                    lk.text = sugkey.text
                    oe = sc.OE
                    lk.oe_id = getGenericElement(oe, self.o)
                    if isinstance(oe, OntologyLiteralElement):
                        lk.triples = oe.triples
                    key_list.append(lk)
            else:
                lk = Key()
                lk.text = sugkey.text
                lk.oe_id = Key.NEIGHBORS_NONE  # No nearest neighbors to question focus were found
                key_list.append(lk)
        return key_list

    def loadLearningVotes(self, learning_keys):
        """
        Generate a list of stored learning votes from a list of learning Keys
        :param learning_keys: list of Key
        :return: list<LearningVote>
        """
        votes = []
        if LEARNING_ENABLED:
            model = loadLearningModel()
            if model:
                for k in learning_keys:
                    key_votes = model.get(k, [])
                    votes.extend(key_votes)
        return votes

    def generateInitialVotes(self, sc_list):
        """
        Generate initial learning votes from a list of Semantic Concepts
        :param sc_list: list<SemanticConcept> to be added to new votes
        :return: list<Vote>
        """
        votes = []
        for sc in sc_list:
            vote = Vote()
            vote.candidate = sc.deepcopy()
            if sc.score is None:
                vote.vote = 1.0
            else:
                vote.vote = float(sc.score)
            votes.append(vote)
        return votes

    def filterClarificationRequired(self):
        """
        Returns whether current query filters need user input to be executed
        :return: True if user must be prompted to clarify filter; False otherwise
        """
        clarification_req = False
        for qf in self.q.filters:
            if isinstance(qf, QueryFilterCardinal):
                if not qf.property and not qf.result:  # Focus of the filter does not exist
                    clarification_req = True
                    break
        return clarification_req

    def disambiguationRequired(self):
        """
        Returns whether an OC disambiguation dialog is currently necessary
        :return: True if user must be prompted to disambiguate ambiguous OCs, False otherwise
        """
        disambiguate = False
        for ocs in self.q.semanticConcepts:
            if len(ocs) > 1 and not overlappingOCsVerified(ocs):
                disambiguate = True
                break
        return disambiguate

    def mappingRequired(self):
        """
        Returns whether an POC to OC mapping dialog is currently necessary
        :return: True if user must be prompted to map a POC to an ontology resource, False otherwise
        """
        mapping = False
        if self.q and self.q.pocs:
            mapping = True
        return mapping
