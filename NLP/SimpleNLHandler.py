import const as c
import re


class SimpleNLHandler(object):

    def __init__(self, NLquery = None):
        if NLquery:
            """ The query as given by the user """
            self.rawQuery = NLquery
            """ The user query after basic normalization """
            self.normalizedFullQuery = self.__normalizeQuery(NLquery)
        else:
            self.rawQuery = None
            self.normalizedFullQuery = None

    def splitCompoundQuery(self, q):
        """
        Divides the query into sub-queries using positive coordinators ('and')
        as dividers
        @return list<string>: A list of sub-queries
        """
        subqueries = []
        if q:
            q = self.__normalizeQuery(q)
            for conj in c.NLNCPosCoordinators:
                divider = " %s " % conj
                subqueries.extend(q.split(divider))
        return subqueries

    def retrieveQualitativeFilters(self, q, exclude = None):
        """
        Tries to find qualitative filters (i.e. labels) within a NL query
        @param q: the NL query
        @param exclude: a list of items (or a single string)
               not to be considered filters
        @return set<string>: A list of inferred filters
        """
        filters = []
        if q:
            if isinstance(exclude, list):
                excludeList = exclude
            else:
                excludeList = list()
                excludeList.append(exclude)
            # Replace underscore to fetch multi-word labels
            labelsTxtRaw = [l.replace("_", " ") for l in re.findall(r"[\w\d']+", q)]
            labelsTxt = [l for l in labelsTxtRaw if l.lower() not in c.NonTags
                         and l not in excludeList]
        return set(labelsTxt)

    def retrieveArithmeticOperation(self, q):
        """
        Tries to find a basic arithmetic operation (e.g. add, sub) within a NL
        query
        @param q: the NL query
        @return (string, (string, string)): first element is the operator found
        or None; second element is a tuple of sub-queries. The operands must be
        recursively found there. N.B. order may be important in non-commutative
        operations
        """
        derivedOp = None
        words = self.__getWords(q)
        lopq = None # left operand query
        ropq = None # right operand query
        for arithOp in c.NLArithmeticBasicOp:
            if arithOp in words:
                derivedOp = c.NLArithmeticBasicOp[arithOp]
                break
        if derivedOp:
            connectors = "|".join(c.NLArithmeticOpConnector)
            regex = "\s*%s\s+(\S.+)\s+(%s)\s+(\S.+)" % (arithOp, connectors)
            p = re.compile(regex)
            m = p.match(q)
            if m:
                connector = m.group(2)
                if connector in c.NLArithmeticOpInvConnector:
                    lopq = m.group(3)
                    ropq = m.group(1)
                else:
                    lopq = m.group(1)
                    ropq = m.group(3)
        return (derivedOp, (lopq, ropq))

    def retrieveCardinalFilters(self, q):
        """
        Tries to find a cardinal filter of attribute values within a NL query
        @param q: the NL query
        @return (string, string): a tuple (operator, operand) to use
        """
        t = (None, None)
        if q:
            negate = any([n in q for n in c.NLopNEG])
            valfilters = "|".join(c.NLAttrValCardFilterOp)
            regex = '.*(' + valfilters + ')\s+(\d+\.?\d*).*'
            p = re.compile(regex)
            m = p.match(q)
            operand = None
            if m:
                operand = unicode(m.group(2)) # Take the number from the regex
            if operand:
                operatorNL = m.group(1).lower().strip()
                if operatorNL in c.NLAttrValCardFilterOp:
                    operator = c.NLAttrValCardFilterOp[operatorNL]
                else:
                    operator = None
                t = (operator, operand)
        return t

    def retrieveDerivedOPFilter(self, q):
        """
        Tries to find a derived operation (e.g. average) within a NL query
        @param q: the NL query
        @return string: the operator found (e.g. avg, count) or None
        """
        derivedOp = None
        words = self.__getWords(q)
        for dop in c.NLDerivedValueOp:
            if dop in words:
                derivedOp = c.NLDerivedValueOp[dop]
                break
        return derivedOp

    def retrieveExtremeOPFilter(self, q):
        """
        Tries to find an operation to retrieve an extreme value (e.g. minimum)
        within a NL query
        @param q: the NL query
        @return string: the operator found (e.g. avg, sum, count...) or None
        """
        op = None
        words = self.__getWords(q)
        for dop in c.LNAttrExtremeOp:
            if dop in words:
                op = c.LNAttrExtremeOp[dop]
                break
        return op

    def retrieveNegate(self, q):
        """
        Returns whether a negation operator is found in the given query
        @param q: the NL query
        @return boolean: True if a negation operator is found; False otherwise
        """
        return any([n in self.__getWords(q) for n in c.NLopNEG])

    def retrieveReverse(self, q):
        """
        Returns whether a reverse sorting operator is found in the given query
        @param q: the NL query
        @return boolean: True if the result is to be reversed; False otherwise
        """
        return not any([s in self.__getWords(q) for s in c.NLsortOpNeg])

    def __getWords(self, q):
        """
        Return the words (alphanumeric strings separated by whitespace)
        from a given sentence
        @param q: the input NL query
        @return list<string>: a list of all words in the query, converted to
        lowercase
        """
        return [w.lower() for w in re.findall("\w+", q)]

    def __normalizeQuery(self, q):
        """
        Performs simple normalization on a given query
        @param q: the NL query
        @return string: the normalized query
        """
        nq = ""
        if q:
            nq = q.lower()
            nq = nq.replace(",", " ")
        return nq