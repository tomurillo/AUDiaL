from Ontovis.upper_ontology import UpperOntology
from Ontovis.bar_chart_ontology import BarChartOntology
from NLP.SimpleNLHandler import *
from NLP.NLHandler import *
from mapper.Mapper import *
from oc.OCUtil import *
from oc.OCCreator import addSemanticConcepts
from consolidator.Consolidator import *
from dialog.dialogHandler import DialogHandler


class Controller(object):

    def __init__(self, type, RDFpath=None):
        """
        Controller constructor
        @param type: domain ontology to be loaded
        @param RDFPath: path to the ontology to be loaded. None to load from
        serialized ontology.
        """
        self.type = type
        self.q = None  # User query and attributes
        self.o = None  # Ontology
        self.NL = SimpleNLHandler()  # Natural Language handler
        self.mapper = Mapper()
        self.consolidator = None
        self.dialogue = None  # Dialogue controller
        if type == c.BAR_CHART:
            self.o = BarChartOntology(RDFpath)
        else:
            self.o = UpperOntology(RDFpath)

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
            # Output dialog
            from dialog.webformat.formatter import SuggestionFormatter
            formatter = SuggestionFormatter(self.o)
            return formatter.suggestionPairToJSON(suggestion_pair)
        else:
            return False

    def parseAndLookUp(self, what):
        """
        Performs the query parsing and ontology lookup steps before consolidation
        After calling this method there will be a fully initialized Query instance in self.q
        :param what: a NL query
        :return: void
        """
        self.NL = NLHandler(self.mapper)
        self.q = self.NL.parseQuery(what)  # Get POCs
        self.q = self.mapper.ontologyBasedLookUp(self.o, self.q)  # Get OCs
        self.q = preConsolidateQuery(self.q, self.o)
        self.q = addSemanticConcepts(self.q)

    def consolidateQuery(self):
        """
        Performs the consolidation step of mapping POCs to OCs, including automatic and manual
        consolidation sub-steps.
        :return: void; self.q is consolidated.
        """
        self.consolidator = Consolidator()
        self.q = self.consolidator.consolidateQuery(self.q)

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
            suggestion = self.processQuery(what)
            if suggestion:
                output_type = 'dialogue'
                output = suggestion
            else:
                pass  # fetch answer TODO
        return output, output_type

    def retrieveValueSimple(self, what):
        """
        Handles a user query related to a filtering of bars according to the
        user-given labels
        @param what: the input query
        """
        output = ""
        if self.type == c.BAR_CHART:
            query = self.NL.splitCompoundQuery(what)
            units = self.o.getChartMeasurementUnit()
            if units:
                unitsNL = units.replace("_", " ").lower()
            else:
                unitsNL = "unknown"
            q = ""
            for subq in query:
                # Remove units to avoid mistaking them for tags
                subq = subq.replace(unitsNL, "")
                q += subq # Combine sub-queries to remove connectors
            filtersInQuery = self.NL.retrieveQualitativeFilters(q)
            if filtersInQuery:
                negate = self.NL.retrieveNegate(q)
                bars = self.o.applyLowLevelTask(self.o.StructuralTask.ReadingTask.FILTER,
                                                filters = filtersInQuery,
                                                negate = negate)
                for bar in bars:
                    output += self.__printBarDetails(bar)
        return output

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
                output += self.__printBarDetails(bar)
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
                            output += self.__printBarDetails(bar)
                            barVal = self.o.getMetricBarValue(bar)
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
                            tags = self.__printBarDetails(bar)
                            output += "%s: Stacked bars maximum: %s. %s" \
                                % (q, value, tags)
                        if op == 'min' or op == 'range':
                            bar, value = infoStacked['min']
                            tags = self.__printBarDetails(bar)
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
                            tags = self.__printBarDetails(bar)
                            output += "%s: Metric bars maximum: %s. %s" \
                                % (q, value, tags)
                        if op == 'min' or op == 'range':
                            bar, value = infoSimple['min']
                            tags = self.__printBarDetails(bar)
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
        @return string: A natural language summary of the graphic
        """
        return self.o.generateSummary()

    def setUserTags(self, usertags, to = 'current'):
        """
        Sets the given user tags to an element of the current graphic
        @param usertags: a string containing the user data
        @to to which element to associate the tags: current (default), previous,
        home.
        @return: string: A natural language description of the operation
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
                output = "Information added to %s bar%s: '%s'.<br/>" % (to,
                                                                      plural,
                                                                      usertags)
        return output

    def navigate(self, action):
        """
        Performs an atomic navigation action on the graphic
        @param string: the action to perform (where, next, previous...)
        @return string: a natural language description of the action's result
        """
        b = None
        output = ""
        if action == 'where':
            b =  self.o.navigate([self.o.StructuralTask.NavigationTask.WHERE])
            if b[0]:
                output += "Current Bar: "
                output += self.__printBarDetails(b[0], skipNav=True)
            else:
                output += " No current bar available!. Please reset the " \
                            "navigation.<br/>"
        elif action == 'next':
            b =  self.o.navigate([self.o.StructuralTask.NavigationTask.MOVE_RIGHT])
            if b[0]:
                output += "Moved to next bar: "
                output += self.__printBarDetails(b[0], skipNav=True)
            else:
                output += "No next bar.<br/>"
        elif action == 'previous':
            b =  self.o.navigate([self.o.StructuralTask.NavigationTask.MOVE_LEFT])
            if b[0]:
                output += "Moved to previous bar: "
                output += self.__printBarDetails(b[0], skipNav=True)
            else:
                output += "No previous bar.<br/>"
        elif action == 'first':
            b =  self.o.navigate([self.o.StructuralTask.NavigationTask.GOTO_FIRST])
            if b[0]:
                output += "Moved to fist bar: "
                output += self.__printBarDetails(b[0], skipNav=True)
            else:
                output += "No first bar available.<br/>"
        elif action == 'last':
            b =  self.o.navigate([self.o.StructuralTask.NavigationTask.GOTO_LAST])
            if b[0]:
                output += "Moved to last bar: "
                output += self.__printBarDetails(b[0], skipNav=True)
            else:
                output += "No last bar available.<br/>"
        elif action == 'highest':
            b =  self.o.navigate([self.o.StructuralTask.NavigationTask.GOTO_HIGHEST])
            if b[0]:
                output += "Moved to bar with highest value: "
                output += self.__printBarDetails(b[0], skipNav=True)
            else:
                output += "Highest bar could not be found.<br/>"
        elif action == 'lowest':
            b =  self.o.navigate([self.o.StructuralTask.NavigationTask.GOTO_LOWEST])
            if b[0]:
                output += "Moved to bar with lowest value: "
                output += self.__printBarDetails(b[0], skipNav=True)
            else:
                output += "Lowest bar could not be found.<br/>"
        elif action == 'up':
            b =  self.o.navigate([self.o.StructuralTask.NavigationTask.MOVE_UP])
            if b[0]:
                output += "Moved one level up: "
                output += self.__printBarDetails(b[0], skipNav=True)
            else:
                output += "You can not go up. Try going next, back or down.<br/>"
        elif action == 'down':
            b =  self.o.navigate([self.o.StructuralTask.NavigationTask.MOVE_DOWN])
            if b[0]:
                output += "Moved one level down: "
                output += self.__printBarDetails(b[0], skipNav=True)
            else:
                output += "You can not go down. Try going next, back or up.<br/>"

        elif action == 'sethome':
            b =  self.o.navigate([self.o.StructuralTask.NavigationTask.SET_HOME])
            if b[0]:
                output += "Current Bar selected as home node.<br/>"
            else:
                output += "The current bar can not be chosen as home node.<br/>"
        elif action == 'gotohome':
            b =  self.o.navigate([self.o.StructuralTask.NavigationTask.GOTO_HOME])
            if b[0]:
                output += "Moved to Home Node: "
                output += self.__printBarDetails(b[0], skipNav=True)
            else:
                output += "No home node found.<br/>"
        elif action == 'reset':
            b =  self.o.navigate([self.o.StructuralTask.NavigationTask.RESET])
            if b[0]:
                output += "Navigation has been reset. Current bar: "
                output += self.__printBarDetails(b[0], skipNav=True)
            else:
                output += "Error while resetting.<br/>"
        return output

    def executeTask(self, task):
        """
        Executes a given task on the current graphic
        @param task: a task instance name
        @return string: the output of the executed task
        """
        taskTypes = self.o.getClassOfElement(task)
        q = self.o.getTaskQuery(task)
        out = None
        outNumeric = None
        addres = False
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

    def __printBarDetails(self, bar, skipNav = False):
        """
        Print a natural-language description of a bar's information, including:
            - Whether it is a simple (metric) or a stacked bar
            - Its textual labels
            - Its value according to the size in relation to the metric axis
            - Its units according to the chart's metric axis
            - Its current user navigation properties, if skipNav is set to False
            - Its user-defined labels
        @param bar (string): a bar instance name
        @param skipNav (boolean): whether to skip user navigation information
               (i.e. if the bar is the current or home bar)
        @return string: a natural-language description of the bar
        """
        output = "Bar not found!<br/>"
        if bar:
            units = self.o.getChartMeasurementUnit()
            if units:
                unitsNL = units.replace("_", " ").lower()
            else:
                unitsNL = "(units unknown)"
            output = ""
            barfilters = self.o.getElementFilters(bar)
            if self.o.elementHasRole(bar, self.o.SyntacticRoles.STACKED_BAR):
                output += "Stacked bar "
            else:
                output += "Simple bar "
            if len(barfilters) > 0:
                output += ' with labels: '
                output += ', '.join(str(v) for v in sorted(barfilters) if v)
            size = self.o.getMetricBarValue(bar)
            output += " (%0.2f %s). " % (size, unitsNL)
            navFilters = self.o.getNavigationProperties(bar)
            for nf in navFilters:
                if not skipNav:
                    if nf == self.o.NavigationDataProperty.IS_CURRENT:
                        output += "This is the current bar. "
                    elif nf == self.o.NavigationDataProperty.IS_HOME_NODE:
                        output += "This is the home bar. "
                if nf == self.o.NavigationDataProperty.HAS_USER_LABEL:
                    ul = navFilters[nf]
                    output += "User tags: %s. " % ul
            output += "<br/>"
        return output

    def __printOutputList(self, generator, *args):
        """
        Takes the output of a given method and its arguments and outputs a
        string of the concatenated results separated by commas
        @param generator: the method to call
        @param args: the arguments to the method
        @returns a comma-separated string of the method's output
        """
        return ",".join([f for f in generator(*args) if f])
            