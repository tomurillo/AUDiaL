class SuggestionKey(object):
    def __init__(self, text=''):
        """
        Dialog Suggestion Key constructor
        """
        self.text = text  # Text that needs clarification
        self.nearest_neighbors = []

    def __eq__(self, other):
            if type(other) is not SuggestionKey:
                return False
            elif self.text != other.text:
                return False
            elif self.nearest_neighbors != other.nearest_neighbors:
                return False
            else:
                return True

    def __ne__(self, other):
        return not self.__eq__(other)
