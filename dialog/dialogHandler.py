from dialog.model.SuggestionKey import *
from dialog.model.SuggestionPair import *
from dialog.model.Key import *
from dialog.model.Vote import *
from dialog.model.modelUtil import *
from dialog.learning.util import *
from oc.OCUtil import *


class DialogHandler(object):
    """
    User/system dialog (disambiguation and mapping) utility class
    """

    class Constants:
        NEIGHBORS_NONE = 'Neighbors_None'

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
        :return:
        """
        if self.disambiguationRequired():
            pass

    def generateDisambiguationDialog(self):
        """
        Generates a user dialog to disambiguate between ambiguous OCs in the query
        :return:
        """
        key = SuggestionKey()
        pair = SuggestionPair()
        next_ocs = nextAmbiguousOCs(self.q)  # OC closest to question focus
        if next_ocs:
            oc_first = next_ocs[0]
            key.text = oc_first.OE.annotation.rawText
        neighbor_ocs = findNearestOCsInQuery(self.q, next_ocs)
        key.nearest_neighbors = neighbor_ocs
        pair.key = key
        #  Search for learning keys in the Ontology and learning votes in the model
        learning_keys = self.generateLearningKeys(key)
        learning_votes = self.generateLearningVotes(learning_keys)
        #  Initialize suggestion pair votes from ambiguous OCs
        suggestion_votes = self.generateInitialVotes(next_ocs)
        #############################
        # TODO
        #############################

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
                    lk.oe_id = getGenericElement(sc.OE, self.o)
                    if isinstance(sc.OE, OntologyLiteralElement):
                        lk.triples = sc.OE.triples
                    key_list.append(lk)
            else:
                lk = Key()
                lk.text = sugkey.text
                lk.oe_id = self.Constants.NEIGHBORS_NONE  # No nearest neighbors to question focus were found
                key_list.append(lk)
        return key_list

    def generateLearningVotes(self, learning_keys):
        """
        Generate a list of stored votes from a list of learning Keys
        :param learning_keys: list of Key
        :return: list<Vote>
        """
        votes = []
        model = loadLearningModel()
        if model:
            for k in learning_keys:
                key_votes = []
                key_str = str(k)
                if key_str in model:
                    key_votes = model[key_str]
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
