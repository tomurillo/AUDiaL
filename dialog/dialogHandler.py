from oc.OCUtil import *


class DialogHandler(object):
    """
    User/system dialog (disambiguation and mapping) utility methods
    """

    def __init__(self, query):
        """
        Dialog Handler constructor.
        :param query: A pre-consolidated Query instance
        :return:
        """
        self.q = query

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
        next_ocs = nextAmbiguousOCs(self.q)  # OC closest to question focus
        neighbor_ocs = findNearestOCsInQuery(self.q, next_ocs)



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

