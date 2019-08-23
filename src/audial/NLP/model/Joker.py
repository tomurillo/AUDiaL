class Joker(object):

    def __init__(self, types=None):
        """
        Joker constructor.
        :param types: List<string>; OntologyElement subclasses that this Joker can match
        """
        self.id = ""
        self.answer = False  # Whether this joker is the query's answer
        if types is None:
            self.suitable_types = []
        else:
            self.suitable_types = types

    def set_id(self, n):
        """
        Sets this instance's id attribute
        :param n: int or string; position of this element within a OC list
        :return: None; updates this instance
        """
        if n == "first":
            self.id = "firstJoker"
        elif n == "last":
            self.id = "lastJoker"
        elif n:
            try:
                self.id = "j%d" % n
            except ValueError:
                from warnings import warn
                warn("Joker ID has been set to a non-numerical value", SyntaxWarning)
                self.id = "j%s" % n
