class SuggestionPair(object):
    def __init__(self):
        """
        Dialog Suggestion Pair constructor
        """
        self.key = None  # SuggestionKey instance
        self.votes = []  # List of Vote
        self.subject = None  # POC instance

    def __eq__(self, other):
            if type(other) is not SuggestionPair:
                return False
            elif self.key != other.key:
                return False
            elif self.votes != other.votes:
                return False
            elif self.subject != other.subject:
                return False
            else:
                return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.key) ^ hash(tuple(self.votes)) ^ hash(self.subject)
