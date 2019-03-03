class Joker(object):

    def __init__(self, types=None):
        """
        Joker constructor.
        :param types: List<string>; OntologyElement subclasses that this Joker can match
        """
        if types is None:
            self.suitable_types = []
        else:
            self.suitable_types = types
