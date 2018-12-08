class SuggestionPair(object):
    def __init__(self):
        """
        Dialog Suggestion Pair constructor
        """
        self.key = None
        self.votes = []
        self.subject = None

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
