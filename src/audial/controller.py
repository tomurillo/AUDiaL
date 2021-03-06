from flask import session
from oc.triple_utils import *
from NLP.parser.CommandParser import *
from NLP.SimpleNLHandler import SimpleNLHandler
from NLP.NLHandler import *
from mapper.Mapper import *
from oc.OCUtil import *
from oc.OCCreator import addSemanticConcepts
from consolidator.Consolidator import *
from dialog.dialogHandler import DialogHandler
from dialog.model.SuggestionPair import SuggestionPair
from logger.Logger import AudialLogger
from config import *
import const as c


class Controller(object):

    def __init__(self, type, RDFpath=None, sess_id='', reload_file=False):
        """
        Controller constructor
        :param type: domain ontology handler to employ
        :param RDFPath: path to the ontology to be loaded. None to load from a serialized ontology according to :sess_id
        :param sess_id: string; session ID to use as prefix for session attributes
        :param reload_file: bool; whether to re-fetch ontology data from the given file
        """
        self.type = type
        if c.SESS_QUERY in session:  # Coming from a dialogue, fetch consolidated query from session
            q = Query()
            q.from_dict(session[c.SESS_QUERY])
            self.q = q
            reload_file = False
        else:
            self.q = None
        self.o = None  # Ontology
        self.NL = SimpleNLHandler()  # Default Natural Language handler if mapper not used
        self.mapper = Mapper(parser=NLP_PARSER, tagger=NLP_POS_TAGGER)
        self.consolidator = None
        self.dialogue = None  # Dialogue controller
        self.logger = AudialLogger()
        if type == c.BAR_CHART:
            self.o = BarChartOntology(RDFpath, sess_id, reload_file)
        else:
            self.o = UpperVisOntology(RDFpath, sess_id, reload_file)

    def isOntologyLoaded(self):
        """
        @return bool: whether the ontology graph is loaded and can be queried
        """
        return self.o.graph is not None

    def clean(self):
        """
        Closes the ontology to prevent memory leaks
        """
        if self.o:
            self.o.close()

    def processQuery(self, what):
        """
        Processes a user's single query in Natural Language, returning a dialog to resolve
        unknown or ambiguous concepts.
        :param what: A single NL phrase
        :return: A suggestion pair if the query cannot be resolved; False otherwise (no dialogue needed; query instance
        is resolved and task needs to be performed next)
        """
        self.parseAndLookUp(what)
        self.consolidateQuery()
        self.dialogue = DialogHandler(self.q, self.o)  # Dialog needs consolidated query
        suggestion_pair = self.dialogue.generateDialogs()
        if suggestion_pair:
            session[c.SESS_SUG_PAIR] = suggestion_pair.to_dict()
            # Output dialog
            formatter = OutputFormatter(self.o, skip_inflect=True)
            return formatter.suggestionPairToJSON(suggestion_pair)
        return False

    def processVote(self, vote_id):
        """
        Processes a user selection of a suggestion from a disambiguation or mapping dialog
        :param vote_id: (string) The ID of the chosen vote
        :return: A suggestion pair if the query cannot be resolved after having considered the vote; False otherwise
        (no further dialogue needed; query instance is resolved and task needs to be performed next)
        """
        from dialog.learning.util import updateVoteScores, updateLearningModel, LEARNING_ENABLED
        suggestion_pair_dict = session.get(c.SESS_SUG_PAIR)
        self.consolidator = Consolidator(self.q)
        if self.q and vote_id and suggestion_pair_dict:
            suggestion_pair = SuggestionPair()
            suggestion_pair.from_dict(suggestion_pair_dict)
            votes_chosen = updateVoteScores(suggestion_pair, vote_id)
            if LEARNING_ENABLED:
                updateLearningModel(suggestion_pair, self.o)
            scs_updated = [v.candidate for v in votes_chosen]  # OCs chosen by the user in dialogue
            if scs_updated:
                self.logger.log_vote(scs_updated[0])
                if suggestion_pair.subject:
                    # It was a POC -> OC mapping dialogue
                    self.q = self.consolidator.resolvePOCtoOC(suggestion_pair.subject, scs_updated)
                elif suggestion_pair.filter:
                    # It was a filter disambiguation
                    self.q = self.consolidator.resolveFilterSubject(suggestion_pair.filter, scs_updated)
                else:
                    # It was a disambiguation dialogue between OCs
                    self.q = self.consolidator.disambiguateOCs(scs_updated)
            #  Call generateDialogs again; query may still have unresolved elements
            self.dialogue = DialogHandler(self.q, self.o)
            suggestion_pair_new = self.dialogue.generateDialogs()
            if suggestion_pair_new:
                session.pop(c.SESS_SUG_PAIR)
                session[c.SESS_SUG_PAIR] = suggestion_pair_new.to_dict()
                # Output dialog
                formatter = OutputFormatter(self.o, skip_inflect=True)
                return formatter.suggestionPairToJSON(suggestion_pair_new)
        return False

    def computeAnswer(self):
        """
        Given a consolidated query, generate an answer from its semantic concepts
        :return: string; answer (or lack thereof) to the user's query
        """
        answer = 'Your query could not be resolved'
        if allOCsShareNamespace(self.q.semanticConcepts, self.o.VIS_NS):
            self.q.filters.extend(self.q.getNominalFilters())
            if isinstance(self.o, BarChartOntology):
                bars = self.o.applyLowLevelTask(self.o.StructuralTask.ReadingTask.APPLY_QFILTER, filters=self.q.filters)
                if bars:
                    if self.q.task:
                        bars = self.o.filterBarsForTask(bars, self.q.task)
                    n = len(bars)
                    n_str = " %d" % n if n > 1 else ''
                    pl_str = 's' if n > 1 else ''
                    v_str = 'have' if n > 1 else 'has'
                    add_summary = False
                    if self.q.task:
                        answer, success = self.o.applyAnalyticalTask(self.q.task, bars)
                        if success and self.o.taskNeedsSummary(self.q.task):
                            add_summary = True
                            answer += '<h5>The following%s bar%s %s been considered:</h5><ul>' % (n_str, pl_str, v_str)
                    else:
                        add_summary = True
                        answer = '<h5>The following%s bar%s matched your query:</h5><ul>' % (n_str, pl_str)
                    if add_summary:
                        sorted_bars = self.o.sortBarsAccordingToNavigation(bars)
                        if n > MAX_OUTPUT_NODES:
                            sorted_bars = sorted_bars[:MAX_OUTPUT_NODES]
                        for bar in sorted_bars:
                            answer += '<li>%s</li>' % self.o.printBarDetails(bar)[0]
                        if n > MAX_OUTPUT_NODES:
                            answer += '<li>And %d more (not shown)</li>' % (n - MAX_OUTPUT_NODES)
                    answer += "</ul>"

                    if not self.q.task:
                        answer += self.__summarizeBars(bars)
                else:
                    answer = 'No bars match your query.'
        else:
            answer = self.fetchAnswerFromDomain()
        return answer

    def fetchAnswerFromDomain(self):
        """
        Query a domain ontology and return answer
        :return:
        """
        if self.q and self.q.ocs_consistent():
            from dialog.config import MAX_RESULTS
            self.q.semanticConcepts = sorted(self.q.semanticConcepts, cmp=SemanticConceptListCompareOffset)
            self.consolidator = Consolidator(self.q)
            self.consolidator.consolidateAnswerType()  # Query is consolidated; fetch answer type first
            scs = self.consolidator.removeDuplicatedSemanticConcepts()
            ocs_for_query = []
            for sc_list in scs:
                ocs = []
                added_ocs = []
                for sc in sc_list:
                    if not isinstance(sc.OE, OntologyNoneElement):
                        if sc.OE.added:
                            added_ocs.append(sc)
                        else:
                            ocs.append(sc)
                for added_oc in added_ocs:
                    for sc in sc_list:
                        if sc.OE.annotation == added_oc.OE.annotation:
                            sc.task = added_oc.task
                if ocs:
                    ocs_for_query.append(ocs)
            prepared_ocs = prepareOCsForQuery(ocs_for_query)
            formal_query = FormalQuery(self.o.getNamespaces(), MAX_RESULTS)
            formal_query.from_concepts(prepared_ocs)  # SPARQL generation
            results = self.o.executeQuery(formal_query.sparql)
            answer = generateDomainAnswer(self.q, formal_query, results, self.o)
            return answer

    def commandLookUp(self, what):
        """
        Performs a first quick parse to find commonly issued commands
        If a task is found; perform it immediately without parsing the query
        :param what: a normalized NL query
        :return: string; command output or None
        """
        output = ''
        quick_parser = CommandParser(what)
        task = quick_parser.queryToTask()
        if task:
            if isinstance(self.o, BarChartOntology):
                if task == self.o.StructuralTask.ReadingTask.SUMMARY:
                    output = self.retrieveSummary()
                else:
                    output = self.navigate(task)
        return output

    def parseAndLookUp(self, what):
        """
        Performs the query parsing and ontology lookup steps before consolidation
        After calling this method there will be a fully initialized Query instance in self.q
        :param what: a NL query
        :return: void
        """
        self.NL = NLHandler(self.mapper)
        self.q = self.NL.parseQuery(what)  # Get POCs
        self.q = self.NL.getCardinalFilters(self.q)  # Get filters
        self.q = self.mapper.ontologyBasedLookUp(self.o, self.q)  # Get OCs
        self.q = preConsolidateQuery(self.q, self.o)
        self.q = addSemanticConcepts(self.q, self.o.sess_id)

    def consolidateQuery(self):
        """
        Performs the automatic consolidation step of mapping POCs to OCs
        :return: void; self.q is consolidated.
        """
        self.consolidator = Consolidator(self.q)
        self.q = self.consolidator.consolidateQuery()

    def count(self,element):
        """
        Returns the number of elements
        """
        return self.o.count(element)

    def retrieveCount(self, element):
        """
        Returns the number of elements in natural language form
        """
        c = self.count(element)
        if c:
            output = '%d elements of type %s have been found' % (c, element)
        else:
            output = 'No elements of type %s have been found' % element
        return output

    def retrieveValue(self, what):
        output = ""
        output_type = 'answer'
        if self.type == c.BAR_CHART:
            self.logger.log_query(what)
            output = self.commandLookUp(what)
            if not output:
                suggestion = self.processQuery(what)
                if suggestion:
                    output_type = 'dialogue'
                    output = suggestion
                    self.logger.log_dialog(output)
                else:
                    output = self.computeAnswer()
                    self.logger.log_answer(output)
        return output, output_type

    def processVoteSelection(self, vote_id):
        output = 'Your selection could not be resolved.'
        output_type = 'answer'
        if self.type == c.BAR_CHART:
            suggestion = self.processVote(vote_id)
            if suggestion:
                output_type = 'dialogue'
                output = suggestion
                self.logger.log_dialog(output)
            else:
                output = self.computeAnswer()
                self.logger.log_answer(output)
        return output, output_type

    def retrieveNumeric(self, what):
        """
        Handles a user query related to a numeric filtering of bars
        @param what: the input query
        @return (string, float) First element is a NL description of the output,
        second element is a numerical representation of the output, or None if
        it can't be expressed numerically.
        """
        output = ""
        outNumeric = None
        if self.type == c.BAR_CHART:
            units = self.o.getChartMeasurementUnit()
            if units:
                unitsNL = units.replace("_", " ").lower()
            else:
                unitsNL = "unknown"
            query = self.NL.splitCompoundQuery(what.replace(unitsNL, ""))
            for q in query:
                negate = self.NL.retrieveNegate(q)
                (operator, operand) = self.NL.retrieveCardinalFilters(q)
                filters = self.NL.retrieveQualitativeFilters(q, exclude=operand)
                bars = self.o.applyLowLevelTask(self.o.StructuralTask.ReadingTask.FILTER,
                                                filters = filters,
                                                operator = operator,
                                                operand = operand,
                                                negate = negate)
            for bar in bars:
                output += self.o.printBarDetails(bar)[0]
            if len(bars) == 1:
                outNumeric = self.o.getMetricBarValue(bars.pop())
        return output, outNumeric

    def retrieveDerivedValue(self, what):
        """
        Handles a user query related to an aggregate numeric representation
        of data cases (filters may be also given in the query)
        e.g. What is the average number of male in Vienna?
        @param what: the input query
        @return (string, (float, float)) First element is a string describing
        the output. Second is a tuple whose first item contains the stacked bars
        result and the second item contains the metric bar results. They can
        be None if no result could be found.
        """
        output = ""
        outputNumeric = (None, None)
        if self.type == c.BAR_CHART:
            query = self.NL.splitCompoundQuery(what)
            for q in query:
                # Try finding an arithmetic operation first, then fetch filters
                # from left and right operand queries
                (arithOp, operands) = self.NL.retrieveArithmeticOperation(q)
                if arithOp:
                    import operator
                    aritOps = { 'add' : operator.add, 'sub' : operator.sub,
                                'mul' : operator.mul, 'div' : operator.div }
                    lopq = operands[0] # left operand query
                    ropq = operands[1] # right operand query
                    if lopq and ropq:
                        # left stacked result, left metric result
                        (_, (lsr, lmr)) = self.retrieveDerivedValue(lopq)
                        # right stacked result, right metric result
                        (_, (rsr, rmr)) = self.retrieveDerivedValue(ropq)
                    else:
                        lsr, lmr, rsr, rmr = (None, ) * 4
                    if lsr is not None and rsr is not None:
                        resStacked = aritOps[arithOp](lsr, rsr)
                    else:
                        resStacked = None
                    if lmr is not None and rmr is not None:
                        resSimple = aritOps[arithOp](lmr, rmr)
                    else:
                        resSimple = None
                    output = ""
                    if resStacked:
                        output += "%s result (stacked bars): %.2f<br/>" \
                                                    % (arithOp, resStacked)
                    if resSimple:
                        output += "%s result (metric bars): %.2f<br/>" \
                                                    % (arithOp, resSimple)
                    if not output:
                        output = "No results found.<br/>"
                    outputNumeric = (resStacked, resSimple)
                else:
                    barsq = self.__applyQueryBarFilters(q)
                    stacked = []
                    simple = []
                    for b in barsq:
                        if self.o.elementHasRole(b, self.o.SyntacticRoles.STACKED_BAR):
                            stacked.append(b)
                        elif self.o.elementHasRole(b, self.o.SyntacticRoles.METRIC_BAR):
                            simple.append(b)
                    derivedOp = self.NL.retrieveDerivedOPFilter(q)
                    outStacked = self.o.applyLowLevelTask(
                           self.o.StructuralTask.ComparisonTask.COMPUTE_DERIVED_VAL,
                           operator=derivedOp,
                           barset=stacked)
                    outSimple = self.o.applyLowLevelTask(
                           self.o.StructuralTask.ComparisonTask.COMPUTE_DERIVED_VAL,
                           operator=derivedOp,
                           barset=simple)
                    if derivedOp == 'avg':
                        if outStacked is not None:
                            meanStacked = "%.2f" % outStacked
                            output += "Stacked bars mean: %s<br/>" % meanStacked
                        if outSimple is not None:
                            meanSimple = "%.2f" % outSimple
                            output += "Metric bars mean: %s<br/>" % meanSimple
                        outputNumeric = (outStacked, outSimple)
                        if not outStacked and not outSimple:
                            output += "No result for query \"%s\"<br/>" % q
                    else:
                        """
                        If there is only one bar in the filtered set,
                        assume the user is trying to fetch its value or
                        details
                        """
                        cont = False
                        if len(stacked) == 1:
                            bar = stacked.pop()
                            cont = True
                        elif len(simple) == 1:
                            bar = simple.pop()
                            cont = True
                        else:
                            output += "Error: No operator found."
                        if cont:
                            output += self.o.printBarDetails(bar)[0]
                            barVal = float(self.o.getMetricBarValue(bar))
                            if stacked:
                                outputNumeric = (barVal, None)
                            else:
                                outputNumeric = (None, barVal)
        return output, outputNumeric

    def retrieveExtreme(self, what = "", op = None):
        """
        Handles a user query related to finding data cases possessing an extreme
        value of an attribute over its range within the data set (filters may
        be also given in the query)
        e.g. What is highest number of male in Vienna?
        @param what: the input query
        @param op: if known, the operator. None to infer from query
        @return (string, (float, float)) First element is a string describing
        the output. Second is a tuple whose first item contains the stacked bars
        result and the second item contains the metric bar results of the last
        sub-query. They can be None if no result could be found.
        """
        output = ""
        outNumStacked = None
        outNumMetric = None
        if self.type == c.BAR_CHART:
            query = self.NL.splitCompoundQuery(what)
            for q in query:
                if op is None:
                    op = self.NL.retrieveExtremeOPFilter(q)
                if op:
                    negate = self.NL.retrieveNegate(q)
                    (operator, operand) = self.NL.retrieveCardinalFilters(q)
                    filters = self.NL.retrieveQualitativeFilters(q, exclude=operand)
                    barsq = self.o.applyLowLevelTask(
                                     self.o.StructuralTask.ReadingTask.FILTER,
                                     filters = filters,
                                     operator = operator,
                                     operand = operand,
                                     negate = negate)
                    stacked = []
                    simple = []
                    for b in barsq:
                        if self.o.elementHasRole(b, self.o.SyntacticRoles.STACKED_BAR):
                            stacked.append(b)
                        elif self.o.elementHasRole(b, self.o.SyntacticRoles.METRIC_BAR):
                            simple.append(b)
                    infoStacked = self.o.applyLowLevelTask(
                       self.o.StructuralTask.ComparisonTask.FIND_EXTREMUM,
                       barset=stacked)
                    infoSimple = self.o.applyLowLevelTask(
                       self.o.StructuralTask.ComparisonTask.FIND_EXTREMUM,
                       barset=simple)
                    if op not in infoStacked or not infoStacked[op]:
                        output = "Stacked bars %s value: no results.<br/>" \
                                                                    % op
                    else:
                        value = None
                        if op == 'max' or op == 'range':
                            bar, value = infoStacked['max']
                            tags = self.o.printBarDetails(bar)[0]
                            output += "%s: Stacked bars maximum: %s. %s" \
                                % (q, value, tags)
                        if op == 'min' or op == 'range':
                            bar, value = infoStacked['min']
                            tags = self.o.printBarDetails(bar)[0]
                            output += "%s: Stacked bars minimum: %s. %s" \
                                % (q, value, tags)
                        if op == 'range':
                            _, value = infoStacked['range']
                            output += "Stacked bars range: %s.<br/>" % value
                        outNumStacked = value
                    if op not in infoSimple or not infoSimple[op]:
                        output = "Metric bars %s value: no results.<br/>" % op
                    else:
                        value = None
                        if op == 'max' or op == 'range':
                            bar, value = infoSimple['max']
                            tags = self.o.printBarDetails(bar)[0]
                            output += "%s: Metric bars maximum: %s. %s" \
                                % (q, value, tags)
                        if op == 'min' or op == 'range':
                            bar, value = infoSimple['min']
                            tags = self.o.printBarDetails(bar)[0]
                            output += "%s: Metric bars minimum: %s. %s" \
                                % (q, value, tags)
                        if op == 'range':
                            _, value = infoSimple['range']
                            output += "Metric bars range: %s.<br/>" % value
                        outNumMetric = value
                else:
                    output += "Your query '%s' could not be understood.<br/>" % q
        outputNumeric = (outNumStacked, outNumMetric)
        return output, outputNumeric

    def retrieveRange(self, what):
        """
        Handles a user query related to finding the span of values within the
        set of data cases and an attribute of interest (filters may be also
        given in the query) e.g. What is range of males in Vienna?
        @param what: the input query
        @return (string, (float, float)) First element is a string describing
        the output. Second is a tuple whose first item contains the stacked bars
        result and the second item contains the metric bar results of the last
        sub-query. They can be None if no result could be found.
        """
        return self.retrieveExtreme(what, 'range')

    def retrieveSorted(self, what):
        """
        Handles a user query related to ranking a set of data cases according
        to some ordinal metric (filters may be also given in the query)
        e.g. sort the number of people in 2014
        @param what: the input query
        @return string: a natural language description of the result.
        """
        output = ""
        if self.type == c.BAR_CHART:
            query = self.NL.splitCompoundQuery(what)
            for q in query:
                negate = self.NL.retrieveNegate(q)
                (op, operand) = self.NL.retrieveCardinalFilters(q)
                filters = self.NL.retrieveQualitativeFilters(q, exclude=operand)
                barsq = self.o.applyLowLevelTask(
                                 self.o.StructuralTask.ReadingTask.FILTER,
                                 filters = filters,
                                 operator = op,
                                 operand = operand,
                                 negate = negate)
                stacked = {}
                simple = {}
                for b in barsq:
                    barVal = self.o.getMetricBarValue(b)
                    if self.o.elementHasRole(b, self.o.SyntacticRoles.STACKED_BAR):
                        stacked[b] = barVal
                    elif self.o.elementHasRole(b, self.o.SyntacticRoles.METRIC_BAR):
                        simple[b] = barVal

                reverse = self.NL.retrieveReverse(q)
                if len(stacked) > 0:
                    import operator
                    output += "%s: sorted stacked bars:<br/>" % q
                    sortedStacked = sorted(stacked.items(),
                                           key=operator.itemgetter(1),
                                           reverse=reverse)
                    for b, v in sortedStacked:
                        output += "%s: %s<br/>" % (self.__printOutputList(
                                                    self.o.getElementFilters,
                                                    b), v)
                    output += "<br/>"
                if len(simple) > 0:
                    import operator
                    output += "%s: sorted metric bars:<br/>" % q
                    sortedSimple = sorted(simple.items(),
                                          key=operator.itemgetter(1),
                                          reverse=reverse)
                    for b, v in sortedSimple:
                        output += "%s: %s<br/>" % (self.__printOutputList(
                                                    self.o.getElementFilters,
                                                    b), v)
                    output += "<br/>"
        return output

    def retrieveSummary(self):
        """
        Returns the summary of the given graphic. Delegated to the domain
        ontology handler.
        :return string: A natural language summary of the graphic
        """
        summary = 'Summary not available'
        if isinstance(self.o, BarChartOntology):
            sum_var = c.SESS_SUMMARY % self.o.sess_id
            if sum_var in session:
                summary = session[sum_var]
            else:
                summary = self.o.generateSummary()
                session[sum_var] = summary
            self.logger.log_answer('Summary fetched.')
        return summary

    def setUserTags(self, usertags, to='current'):
        """
        Sets the given user tags to an element of the current graphic
        :param usertags: a string containing the user data
        :param to: to which element to associate the tags: current (default), previous, home.
        :return: string: A natural language description of the operation
        """
        output = "Operation could not be performed. <br/>"
        tags = ""
        if usertags is None:
            usertags = ""
        if self.type == c.BAR_CHART:
            bar = None
            if to == 'current':
                barlist = [self.o.getCurrentBar()]
            elif to == 'previous':
                barlist = self.o.getPreviousNodes()
            elif to == 'home':
                barlist = self.o.getHomeNodes()
            else:
                barlist = []
            if len(barlist) > 0:
                self.o.setUserLabels(barlist, usertags)
                plural = "s" if len(barlist) > 0 else ""
                output = "Information added to %s bar%s: '%s'.<br/>" % (to, plural, usertags)
        return output

    def navigate(self, action):
        """
        Performs an atomic navigation action on the graphic
        :param action: string; the action to perform (where, next, previous...). May also be a formal task
        instance name
        :return string: a natural language description of the action's result
        """
        output = ""
        node_name = "node"
        b = None
        moved = True
        compare_home = True
        action_valid = True
        if isinstance(self.o, BarChartOntology):
            node_name = "bar"
        if action in ['where', self.o.StructuralTask.NavigationTask.WHERE]:
            b = self.o.navigate([self.o.StructuralTask.NavigationTask.WHERE])
            if b[-1]:
                output += "Current %s: " % node_name
                if isinstance(self.o, BarChartOntology):
                    output += self.o.printBarDetails(b[-1], skipNav=True)[0]
            else:
                output += " No current %s available!. Please reset the navigation." % node_name
                moved = False
        elif action in ['next', self.o.StructuralTask.NavigationTask.MOVE_RIGHT]:
            b = self.o.navigate([self.o.StructuralTask.NavigationTask.MOVE_RIGHT])
            if len(b) > 1:
                output += "Moved to next %s: " % node_name
                output += self.o.printPath(b, skipNav=True)
            else:
                output += "No next %s." % node_name
                moved = False
        elif action in ['previous', self.o.StructuralTask.NavigationTask.MOVE_LEFT]:
            b = self.o.navigate([self.o.StructuralTask.NavigationTask.MOVE_LEFT])
            if len(b) > 1:
                output += "Moved to previous %s: " % node_name
                output += self.o.printPath(b, skipNav=True)
            else:
                output += "No previous %s." % node_name
        elif action in ['first', self.o.StructuralTask.NavigationTask.GOTO_FIRST]:
            b = self.o.navigate([self.o.StructuralTask.NavigationTask.GOTO_FIRST])
            if b[-1]:
                output += "Moved to first %s: " % node_name
                output += self.o.printPath(b, skipNav=True)
            else:
                output += "No first %s available.<br/>" % node_name
                moved = False
        elif action in ['last', self.o.StructuralTask.NavigationTask.GOTO_LAST]:
            b = self.o.navigate([self.o.StructuralTask.NavigationTask.GOTO_LAST])
            if b[-1]:
                output += "Moved to last %s: " % node_name
                output += self.o.printPath(b, skipNav=True)
            else:
                output += "No last %s available." % node_name
                moved = False
        elif action in ['highest', self.o.StructuralTask.NavigationTask.GOTO_HIGHEST]:
            b = self.o.navigate([self.o.StructuralTask.NavigationTask.GOTO_HIGHEST])
            if b[-1]:
                output += "Moved to %s with highest value: " % node_name
                output += self.o.printPath(b, skipNav=True)
            else:
                output += "Highest %s could not be found." % node_name
                moved = False
        elif action in ['lowest', self.o.StructuralTask.NavigationTask.GOTO_LOWEST]:
            b = self.o.navigate([self.o.StructuralTask.NavigationTask.GOTO_LOWEST])
            if b[-1]:
                output += "Moved to %s with lowest value: " % node_name
                output += self.o.printPath(b, skipNav=True)
            else:
                output += "Lowest %s could not be found." % node_name
                moved = False
        elif action in ['up', self.o.StructuralTask.NavigationTask.MOVE_UP]:
            b = self.o.navigate([self.o.StructuralTask.NavigationTask.MOVE_UP])
            if len(b) > 1 and b[-1]:
                output += "Moved one level up: "
                output += self.o.printPath(b, skipNav=True)
            else:
                output += "You can not go up, you are in a stacked bar. "
                output += "Try going to the previous or next stacked bar, "
                output += "or visiting this bar's children by going one level down."
                moved = False
        elif action in ['down', self.o.StructuralTask.NavigationTask.MOVE_DOWN]:
            b = self.o.navigate([self.o.StructuralTask.NavigationTask.MOVE_DOWN])
            if len(b) > 1 and b[-1]:
                output += "Moved one level down: "
                output += self.o.printPath(b, skipNav=True)
            else:
                output += "You can not go up, you are in a child bar already. "
                output += "Try going to the previous or next bar, "
                output += "or visiting this bar's parent stacked bar by going one level up."
                moved = False
        elif action in ['sethome', self.o.StructuralTask.NavigationTask.SET_HOME]:
            moved = False
            compare_home = False
            b = self.o.navigate([self.o.StructuralTask.NavigationTask.SET_HOME])
            if b[-1]:
                output += "Current %s selected as home node." % node_name
            else:
                output += "The current %s can not be chosen as home node.<br/>" % node_name
        elif action in ['gotohome', self.o.StructuralTask.NavigationTask.GOTO_HOME]:
            compare_home = False
            b = self.o.navigate([self.o.StructuralTask.NavigationTask.GOTO_HOME])
            if b[-1]:
                output += "Moved to Home %s: " % node_name
                output += self.o.printPath(b, skipNav=True)
            else:
                output += "No home %s found." % node_name
                moved = False
        elif action in ['reset', self.o.StructuralTask.NavigationTask.RESET]:
            moved = False
            compare_home = False
            b = self.o.navigate([self.o.StructuralTask.NavigationTask.RESET])
            if b[-1]:
                output += "Navigation has been reset. Current %s: " % node_name
                if isinstance(self.o, BarChartOntology):
                    output += self.o.printBarDetails(b[-1], skipNav=True)[0]
            else:
                output += "Error while resetting."
        else:
            action_valid = False
        if moved and b:
            output += "<br/>"
            if compare_home:
                home_bars = self.o.getHomeNodes()
                if home_bars and b[-1] not in home_bars and b[0] not in home_bars:
                    output += self.o.printCompareToHome(b[-1])
        if action_valid:
            self.logger.log_command(action, output)
        return output

    def executeTask(self, task):
        """
        Executes a given task on the current graphic
        @param task: a task instance name
        @return string: the output of the executed task
        """
        taskTypes = self.o.getClassOfElement(task)
        q = self.o.getTaskQuery(task)
        outNumeric = None
        # Low-level task
        if self.o.StructuralTask.ReadingTask.FILTER in taskTypes:
            out, outNumeric = self.retrieveNumeric(q)
        elif self.o.StructuralTask.ComparisonTask.COMPUTE_DERIVED_VAL in taskTypes:
            out, outNumeric = self.retrieveDerivedValue(q)
        elif self.o.StructuralTask.ComparisonTask.FIND_EXTREMUM in taskTypes:
            out, outNumeric = self.retrieveExtreme(q)
        elif self.o.StructuralTask.ComparisonTask.RANGE in taskTypes:
            out, outNumeric = self.retrieveRange(q)
        elif self.o.StructuralTask.ComparisonTask.SORT in taskTypes:
            out = self.retrieveSorted(q)
        elif (self.o.CombinationTask.COMPOSITION in taskTypes or
             self.o.CombinationTask.SUPERIMPOSITION in taskTypes):
                subtasks = self.o.getSubTasks(task)
                out = ""
                for i in sorted(subtasks):
                    out += self.executeTask(subtasks[i])
        else:
            raise Exception("Task '%s' not supported!" % task)
        if out:
            rsp = self.o.TaskProperty.HAS_RESULT_SPOKEN
            self.o.removeDataTypePropertyTriple(task, rsp)
            self.o.addDataTypePropertyTriple(task, rsp, out)
        if outNumeric:
            rnp = self.o.TaskProperty.HAS_RESULT_NUMERICAL
            self.o.removeDataTypePropertyTriple(task, rnp)
            self.o.addDataTypePropertyTriple(task, rnp, outNumeric)
        return out

    def getAuthorIntentions(self, forceExecute=False):
        """
        Returns information about the author's intentions according to task
        instances in the current ontology.
        @param forceExecute: whether to execute the tasks instead of fetching
        the data from its properties.
        @return a dictionary with the following structure:
        - Key (int): intention (high-level task) order
        - Value: the following dictionary:
        --- Key: 'summary'; Value: the NL summary of the intention
        ----Key: 'operations'
        ----Value: A dictionary of low-level tasks with the structure:
        -----Key (int): low-level task order
        -----Value: a dictionary with the structure:
        -------Key: 'query'; Value: low-level task NL query
        -------Key: 'spokenresult'; Value: low-level task NL result
        """
        intentions = {}
        intTasks = self.o.getIntentionTasks()
        for i, t in enumerate(intTasks):
            if forceExecute:
                self.executeTask(t)
            intentions[i] = {}
            intentions[i]['summary'] = self.o.getTaskSummary(t)
            t_subdesc = {}
            t_subtasks = self.o.getSubTasks(t)
            for j in sorted(t_subtasks):
                t_subdesc[j] = {}
                t_subdesc[j]['query'] = self.o.getTaskQuery(t_subtasks[j])
                res = self.o.getTaskSpokenResult(t_subtasks[j])
                if not res and not forceExecute:
                    self.executeTask(t_subtasks[j])
                    res = self.o.getTaskSpokenResult(t_subtasks[j])
                t_subdesc[j]['spokenresult'] = res
            intentions[i]['operations'] = t_subdesc
        return intentions

    def __applyQueryBarFilters(self, q, bars=None):
        """
        Apply bar filters (both qualitative and cardinal) from a simple query
        to the given or all bars in a  bar chart
        @param q: a simple NL subquery
        @param bars: the set of bars to take into account; None for all
        @return set<string> a set of filtered bars
        """
        negate = self.NL.retrieveNegate(q)
        (operator, operand) = self.NL.retrieveCardinalFilters(q)
        filters = self.NL.retrieveQualitativeFilters(q, exclude=operand)
        barsq = self.o.applyLowLevelTask(
                         self.o.StructuralTask.ReadingTask.FILTER,
                         filters = filters,
                         operator = operator,
                         operand = operand,
                         negate = negate,
                         barset = bars)
        return barsq

    def __summarizeBars(self, bars):
        """
        Return a bar summary to be given at the beginning of an answer outputting more than one bar
        :param bars: list<string> bar instance names
        :return: string; short summary
        """
        summary = ''
        val = 0.0
        n = len(bars)
        if n > 1:
            for b in bars:
                val += float(self.o.getMetricBarValue(b))
            summary = 'Total value: %0.2f<br/>' % val
            summary += 'Average value: %0.2f<br/>' % (val / n)
        return summary

    def saveContextToSession(self):
        """
        Stores the current execution context into the session
        :return: None, session object gets updated
        """
        if self.q:
            session[c.SESS_QUERY] = self.q.to_dict()
            session.modified = True

    def clearSessionContext(self):
        """
        Clears query-related information from the user's session
        :return: None, session object gets updated
        """
        if c.SESS_QUERY in session:
            session.pop(c.SESS_QUERY)
            self.q = None
        if c.SESS_SUG_PAIR in session:
            session.pop(c.SESS_SUG_PAIR)

    def __printOutputList(self, generator, *args):
        """
        Takes the output of a given method and its arguments and outputs a
        string of the concatenated results separated by commas
        @param generator: the method to call
        @param args: the arguments to the method
        @returns a comma-separated string of the method's output
        """
        return ",".join([f for f in generator(*args) if f])