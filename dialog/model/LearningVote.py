import uuid

class LearningVote(object):
    def __init__(self):
        """
        LearningVote constructor
        """
        self.id = str(uuid.uuid4())
        self.score = -1
        self.function = None

    def __eq__(self, other):
            if not isinstance(other, LearningVote):
                return False
            elif self.id != other.id:
                return False
            elif self.score != other.score:
                return False
            elif self.function != other.function:
                return False
            else:
                return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.id) ^ hash(self.score) ^ hash(self.score) ^ hash((self.id, self.function))
