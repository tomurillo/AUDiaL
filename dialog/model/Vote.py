import uuid


class Vote(object):
    def __init__(self):
        """
        Vote constructor
        """
        self.id = str(uuid.uuid4())
        self.vote = -1.0
        self.candidate = None  # Candidate SemanticConcept instance

    def __eq__(self, other):
            if not isinstance(other, Vote):
                return False
            elif self.id != other.id:
                return False
            elif self.vote != other.vote:
                return False
            elif self.candidate != other.candidate:
                return False
            else:
                return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.id) ^ hash(self.vote) ^ hash(self.candidate)
