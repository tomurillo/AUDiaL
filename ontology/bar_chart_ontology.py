from ontology.upper_vis_ontology import UpperVisOntology, NavigationException
from NLP.model.QueryFilter import QueryFilterCardinal, QueryFilterNominal
from NLP.util.TreeUtil import quick_norm
from sys import float_info
from rdflib import XSD
from general_util import isNumber, stringOpToPython, numberToOrdinal, replaceLastCommaWithAnd


class BarChartOntology(UpperVisOntology):
    """
    Bar Chart Ontology handler; subclass of Upper Visualization Ontology for handling bar charts
    """
    def __init__(self, RDFPath, sess_id='', reload=False):
        """
        BarChartOntology constructor
        :param RDFpath: string; path to an RDF ontology file
        :param sess_id: string; session ID to use as prefix for session attributes
        :param reload: bool; whether to re-fetch ontology data from the given file
        """
        super(BarChartOntology, self).__init__(RDFPath, sess_id, reload)

    def applyAnalyticalTask(self, task_sc, bars):
        """
        Apply an analytical task to the given bars
        :param task_sc: SemanticConcept instance with the task
        :param bars: list<string> bars to which the task will be applied
        :return: (string, boolean); answer in NL and whether the task could be computed
        """
        answer = ''
        success = True
        add_units = True
        numeric_result = None
        units = self.getChartMeasurementUnit()
        if units:
            units_answer = ' %s' % units
        else:
            units_answer = ''
        add_labels_bar = []  # Bars of which to add labels to output
        task = self.stripNamespace(task_sc.task)
        if task == self.StructuralTask.DerivedValueTask.COMPARE:
            answer, success = self.computeCompare(bars)
            add_units = False
        elif task == self.StructuralTask.NavigationTask.JUMP:
            answer = self.computeJumpToBar(bars)
            success = bool(answer)
            add_units = False
        elif task == self.StructuralTask.DerivedValueTask.AVERAGE:
            numeric_result = self.computeDerived('avg', bars)
            if numeric_result is not None:
                answer = 'The average is %.2f' % float(numeric_result)
        elif task == self.StructuralTask.DerivedValueTask.MEDIAN:
            numeric_result = self.computeDerived('median', bars)
            if numeric_result is not None:
                answer = 'The median is %.2f' % float(numeric_result)
        elif task == self.StructuralTask.DerivedValueTask.MODE:
            numeric_result = self.computeDerived('mode', bars)
            if numeric_result is not None:
                answer = 'The most common bar value is %.2f' % float(numeric_result)
        elif task == self.StructuralTask.DerivedValueTask.SUM:
            s = self.computeDerived('sum', bars)
            if s is not None:
                answer = 'The sum of these bars is %.2f' % float(s)
        elif task == self.StructuralTask.DerivedValueTask.COUNT:
            add_units = False
            c = self.computeDerived('count', bars)
            answer = '%d bars match your query.' % c
        elif task == self.StructuralTask.ComparisonTask.FIND_MAXIMUM:
            res = self.computeExtreme('max', bars, 'all')
            if res and 'max' in res:
                add_labels_bar = res['max']
                if add_labels_bar:
                    answer = "The maximum value is: %.2f" % add_labels_bar[0][1]
                else:
                    answer = "No maximum could be found."
                    add_units = False
        elif task == self.StructuralTask.ComparisonTask.FIND_MINIMUM:
            res = self.computeExtreme('min', bars, 'all')
            if res and 'min' in res:
                add_labels_bar = res['min']
                if add_labels_bar:
                    answer = "The mininum value is: %.2f" % add_labels_bar[0][1]
                else:
                    answer = "No minimum could be found."
                    add_units = False
        elif task in [self.StructuralTask.ComparisonTask.FIND_EXTREMUM, self.StructuralTask.ComparisonTask.RANGE]:
            res = self.computeExtreme(['max', 'min'], bars, 'all')
            add_units = False
            if task == self.StructuralTask.ComparisonTask.RANGE and 'range' in res:
                _, r = res['range']
                answer = 'Range of bars is: %.2f' % r
                answer += units_answer
                answer += '. It has the following extreme values:<br/>'
            if res and 'min' in res:
                bar, value = res['min'][0]
                answer += "Minimum value: %.2f" % value
                if task == self.StructuralTask.ComparisonTask.FIND_EXTREMUM:
                    answer += units_answer
                answer += " %s<br/>" % self.getElementFiltersString(bar)
            if res and 'max' in res:
                bar, value = res['max'][0]
                answer += "Maximum value : %.2f" % value
                if task == self.StructuralTask.ComparisonTask.FIND_EXTREMUM:
                    answer += units_answer
                answer += " %s" % self.getElementFiltersString(bar)
        elif task == self.StructuralTask.ComparisonTask.SORT:
            answer = self.computeSort(bars)
            add_units = False
        elif task == self.StructuralTask.DistributionTask.CHARACTERIZE_DISTRIBUTION:
            answer, success = self.computeDistribution(bars)
            add_units = False
        elif task == self.StructuralTask.CorrelationTask.CLUSTER:
            answer, success = self.computeClustering(bars)
            add_units = False
        elif task == self.StructuralTask.DistributionTask.FIND_ANOMALIES:
            answer, success = self.computeFindAnomalies(bars)
            add_units = False
        if answer:
            if add_units and units:
                answer += units_answer
            add_list_markup = len(add_labels_bar) > 1
            if add_list_markup:
                answer += ". There is a tie between the following %d bars:<br/>" % len(add_labels_bar)
            answer += "<ol>" if add_list_markup else ''
            for b, _ in add_labels_bar:
                answer += "<li>Labels: " if add_list_markup else ''
                answer += " %s" % self.getElementFiltersString(b, add_brackets=not add_list_markup)
                answer += "</li>" if add_list_markup else ''
            answer += "</ol>" if add_list_markup else ''
            answer += '<br/>'
            if numeric_result is not None:
                cmp_home = self.printCompareValToHome(numeric_result)
                if cmp_home:
                    answer += "%s<br/>" % cmp_home
        return answer, success

    def navigate(self, actions, bars=None):
        """
        Performs a navigation action in the bar chart.
        @param actions: a list of the following actions, to be done in order:
            'next': move to next bar (of the same role as current)
            'previous': move to previous bar  (of the same type)
            'first': move to the first (pref. stacked) bar
            'last': move to the last (pref. stacked) bar
            'highest': move to the (pref. stacked) bar of highest val
            'lowest': move to the (pref. stacked) bar of lowest val.
            'up': in a metric bar, go to its parent stacked bar
            'down': in a stacked bar, go to its first metric child bar
            'where': return information about current bar
            'reset': reset navigation data
            'set-home': set current bar as home node
        @param bars: a list of bar instances to take into account; None for all
        @return A list of the bars that have been navigated, in order. N.B. some
        of the results might be None when no result is available.
        """
        outputbars = []
        for action in actions:
            if action == self.StructuralTask.NavigationTask.WHERE:
                b = [self.getCurrentBar()]
            elif action == self.StructuralTask.NavigationTask.MOVE_RIGHT:
                b = self.__moveNext()
            elif action == self.StructuralTask.NavigationTask.MOVE_LEFT:
                b = self.__movePrev()
            elif action == self.StructuralTask.NavigationTask.MOVE_UP:
                b = self.__moveUp()
            elif action == self.StructuralTask.NavigationTask.MOVE_DOWN:
                b = self.__moveDown()
            elif action == self.StructuralTask.NavigationTask.GOTO_FIRST:
                b = self.__moveFirst()
            elif action == self.StructuralTask.NavigationTask.GOTO_LAST:
                b = self.__moveLast()
            elif action == self.StructuralTask.NavigationTask.GOTO_HIGHEST:
                b = self.__moveHighest()
            elif action == self.StructuralTask.NavigationTask.GOTO_LOWEST:
                b = self.__moveLowest()
            elif action == self.StructuralTask.NavigationTask.RESET:
                b = self.resetNavigation()
            elif action == self.StructuralTask.NavigationTask.SET_HOME:
                b = self.__setCurrentAsHome()
            elif action == self.StructuralTask.NavigationTask.GOTO_HOME:
                b = self.__goToHome()
            else:
                raise Exception("Action '%s' not supported!" % action)
            outputbars.extend(b)
        return outputbars

    def generateSummary(self):
        """
        Outputs a text summary of the contents of the chart
        """
        output = "This is a bar chart. "

        title = self.getChartTitle()
        if title:
            output += "Its title is: %s <br/>" % title
        else:
            output += "It has no title. <br/>"

        output += "Its main (value) axis describes "
        units = self.getChartMeasurementUnit()
        output += units

        output += "<br/>"
        output += self.getAxisDescription()
        output += self.getLegendsDescription()

        metric_bars = self.getMetricBars()
        n_m = len(metric_bars)
        stacked_bars = self.getStackedBars()
        labels_all = set(self.getLabels())

        if stacked_bars:
            labels_metric = set()
            for b in metric_bars:
                labels_metric |= self.getElementFilters(b, returnText=False)
            labels_stacked = set()
            n_s = 0
            for b in stacked_bars:
                labels_stacked |= self.getElementFilters(b, returnText=False)
                n_s += 1
            labels_metric = labels_metric - labels_stacked
            l_m_str = replaceLastCommaWithAnd(", ".join(self.getText(l) for l in labels_metric))
            n_m_s = n_m / n_s
            output += "There are %d stacked bars, each of which is made up of %d sub-bars" % (n_s, n_m_s)
            if l_m_str:
                output += " (%s)" % l_m_str
            output += ". There is a combined (metric + stacked) total of %d bars." % (n_s + n_m)
        else:
            output += "There are %d bars in the chart. They are all simple metric bars." % n_m
        output += "<br/>"

        lineups = self.getBarLineups()  # Bar line-ups. In simple (ungrouped) bar charts there is only one
        lcount = len(lineups)
        if lcount > 1:
            output += ("The chart has its bars grouped into %d subsets:<br/>" % lcount)

        for l, bars in lineups.iteritems():
            # Try to find the common label of the lineup
            labels = labels_all.copy()
            # Bar individual labels (excluding labels common to all the bars in the lineup)
            specificLabels = {}
            stacked = []
            simple = []
            for b in bars:
                barLabels = self.getElementFilters(b, returnText=False)
                labels &= barLabels
                specificLabels[b] = barLabels
            for b in bars:
                specificLabels[b] = specificLabels[b] - labels  # Remove common labels to the lineup
                if self.elementHasRole(b, self.SyntacticRoles.STACKED_BAR):
                    stacked.append(b)
                elif self.elementHasRole(b, self.SyntacticRoles.METRIC_BAR):
                    simple.append(b)
            stackedMean = self.computeDerived('avg', stacked)
            if labels:
                lbloutput = ",".join([self.getText(l) for l in labels])
                output += "Subset %s:<br/>" % lbloutput
            else:
                output += " All bars:<br/>"
            if stackedMean is not None:
                output += " Mean of stacked bars: %.2f %s<br/>" % (stackedMean, units)
            # Navigate through stacked bars and output averages
            output += "This subset (%s) is further divided into:<br/>" % lbloutput
            for b in stacked:
                specificLblTxt = [self.getText(l) for l in specificLabels[b]]
                output += ", ".join(specificLblTxt) + "<br/>"

        output += "Extreme values of graph:<br/>"

        extremeMetric = self.computeExtreme(['max', 'min'], self.getMetricBars(), 'all')
        extremeStacked = self.computeExtreme(['max', 'min'], self.getStackedBars(), 'all')
        if extremeStacked:
            bar, value = extremeStacked['max'][0]
            tags = ", ".join(sorted([f for f in self.getElementFilters(bar) if f]))
            output += "Stacked bars maximum: %.2f (tags: %s)" % (value, tags)
            if len(extremeStacked['max']) > 1:
                output += ". Tied with %s other bars." % (len(extremeStacked['max']) - 1)
            output += "<br/>"
            bar, value = extremeStacked['min'][0]
            tags = ",".join(sorted([f for f in self.getElementFilters(bar) if f]))
            output += "Stacked bars minimum: %.2f (tags: %s)" % (value, tags)
            if len(extremeStacked['min']) > 1:
                output += ". Tied with %s other bars." % (len(extremeStacked['min']) - 1)
            output += "<br/>"
        if extremeMetric:
            bar, value = extremeMetric['max'][0]
            tags = ", ".join(sorted([f for f in self.getElementFilters(bar) if f]))
            output += "Metric bars maximum: %.2f (tags: %s)" % (value, tags)
            if len(extremeMetric['max']) > 1:
                output += ". Tied with %s other bars." % (len(extremeMetric['max']) - 1)
            output += "<br/>"
            bar, value = extremeMetric['min'][0]
            tags = ", ".join(sorted([f for f in self.getElementFilters(bar) if f]))
            output += "Metric bars minimum: %.2f (tags: %s)" % (value, tags)
            if len(extremeMetric['min']) > 1:
                output += ". Tied with %s other bars." % (len(extremeMetric['min']) - 1)
            output += "<br/>"

        output += "End of summary.<br/>"
        return output

    def getBars(self):
        """
        Returns all bars in the chart, both metric and stacked
        @return: A list of metric bar instance names
        """
        return self.getStackedBars() + self.getMetricBars()

    def getMetricBars(self):
        """
        Returns the metric bars in the chart
        @return: A list of metric bar instance names
        """
        return self.getElementsWithRole(self.SyntacticRoles.METRIC_BAR)

    def getStackedBars(self):
        """
        Returns the stacked bars in the chart
        @return: A list of stacked bar instance names
        """
        return self.getElementsWithRole(self.SyntacticRoles.STACKED_BAR)

    def filterBarsWithValues(self, filters = None, op = None, operand = None,
                            negate = False, barset = None):
        """
        Return the bars with the given qualitative filters and a certain value
        after comparing it to a given value with a given operator.
        @param filters: a list of qualitative filters (labels)
        @param op: the operator e.g. '>', '<', '=', '>=', '<='
        @param operand: a numeric operand (will be casted to float)
        @param negate: whether to logically negate the given operand
        @param barset: the bars to take into account. None (default) for all
        @return: a set of bar instance names
        """
        barset = self.__filterBarsWithFilters(filters, negate, barset=barset)
        op = stringOpToPython(op, negate)
        if operand is not None and op:
            filtered = set()
            for bar in barset:
                l = float(self.getMetricBarValue(bar))
                if op(l, float(operand)):
                    filtered.add(bar)
            return filtered
        elif operand is None:
            return barset
        else:
            raise Exception("Filter: operator '%s' not supported" % op)

    def getElementFiltersString(self, element, add_brackets=True):
        """
        Returns a textual representation of the given element's filters
        :param element: the name of a metric bar instance
        :param add_brackets: whether to add (labels: ...) to the output (True) or just return the filters (False)
        :return: string; comma-separated list of filters for the element e.g. (labels: label_1, label_2)
        """
        filters = self.getElementFilters(element)
        if filters:
            labels = ", ".join(sorted([f for f in filters if f], key=str.lower))
            if add_brackets:
                text = "(labels: %s)" % replaceLastCommaWithAnd(labels)
            else:
                text = replaceLastCommaWithAnd(labels)
        else:
            if add_brackets:
                text = '(no labels found)'
            else:
                text = ''
        return text

    def getBarsOrders(self, bars = None):
        """
        Returns a dictionary of all bars indexed by their navigational order
        @bars: an iterable containing bar instance names; None for all
        @return dict<int,string>: key: navigation order; value: bar instance
        """
        bardict = {}
        if bars is None:
            bars = self.getBars()
        for bar in bars:
            n = self.getValue(bar, self.NavigationDataProperty.HAS_ORDER)
            if n:
                bardict[int(n)] = bar
        return bardict

    def getMetricBarValue(self, metricBar):
        """
        Retrieves the cardinal value of a metric bar as given by its size
        relative to the chart's axis
        @param metricBar: the name of a metric or stacked bar instance
        @return float: the value of the bar (same units as the axis)
        """
        value = None
        axis = self.getMetricAxis()
        if axis:
            dtype = self.getChartMeasurementDataType(axis)
            axisLength = self.lengthOfAxis(axis)
            (topl, bottoml) = self.getExtremeLabels(axis)
            if not topl:
                axisLength = self.computeAxisLengthFromLabels(axis)
                (topl, bottoml) = self.getExtremeLabels(axis)
                if not topl:
                    raise Exception("Axis not correctly labeled: top label not found.")
        else:
            raise Exception("Axis not found in chart.")
        length = self.lengthOfElement(metricBar)
        if axisLength > 0 and length > 0:
            bottomval = float(self.getText(bottoml)) if bottoml else 0.0
            topval = float(self.getText(topl))
            value = abs(topval - bottomval) * (length / axisLength) + bottomval
            if dtype == "int":
                value = int(round(value))
        return value

    def reasonLabelsFromLegends(self):
        """
        Add labels of the bars in the chart according to its legends
        :return: None, updates knowledge base
        """
        legends = self.getLegends()
        color_label_map = {}
        for legend in legends:
            if not self.getValue(legend, self.ReasonerDataPropery.LEGEND_REASONED, default=False):
                legendElements = self.getLegendPairs(legend)
                for subelement, label in legendElements:
                    elementColor = self.getValue(subelement,
                                                 self.SyntacticProperty.HAS_COLOR)
                    if elementColor:
                        if elementColor in color_label_map:
                            color_labels = color_label_map[elementColor]
                        else:
                            color_labels = []
                            color_label_map[elementColor] = color_labels
                        color_labels.append(label)
        if color_label_map:
            bars = self.getMetricBars()
            for b in bars:  # This may take a while
                bar_color = self.getValue(b, self.SyntacticProperty.HAS_COLOR)
                if bar_color:
                    for label in color_label_map.get(bar_color, []):
                        self.addObjectPropertyTriple(b, self.SyntacticProperty.IS_LABELED_BY, label)
            for legend in legends:
                self.addDataTypePropertyTriple(legend, self.ReasonerDataPropery.LEGEND_REASONED, True,
                                               datatype=XSD.boolean,
                                               functional=True)

    def lengthOfElement(self, element):
        """
        Returns the length of a given element, including stacked bars made up of metric bars
        @param element: the name of an instance in the ontology
        @return float: the length of the element, -1 if not found
        """
        length = -1.0
        if element:
            if self.elementHasRole(element, self.SyntacticRoles.STACKED_BAR):
                l = self.lengthOfStackedBar(element)
            else:
                l = super(BarChartOntology, self).lengthOfElement(element)
            if l:
                length = float(l)
        return length

    def lengthOfStackedBar(self, element):
        """
        Returns the length of a given stacked bar instance. If it does not exist,
        it is computed by adding the lengths of the constituent bars.
        @param element: the name of an instance (stacked bar) in the ontology
        @return float: the length of the element
        """
        l = self.getValue(element, self.SytacticDataProperty.HAS_LENGTH)
        if not l:
            length = 0
            subElements = self.getMetricBarsOfStacked(element)
            for e in subElements:
                elmLength = self.lengthOfElement(e)
                if elmLength > 0:
                    length += elmLength
            self.addDataTypePropertyTriple(element, self.SytacticDataProperty.HAS_LENGTH, length, datatype = XSD.float,
                                           functional=True)
        else:
            length = float(l)
        return length

    def getMetricBarsOfStacked(self, bar):
        """
        Returns the metric sub-bars that make up a given stacked bar
        :param bar: the name of a stacked bar instance
        :return list<string>: a list of metric bar instances
        """
        subElements = []
        elementsWithSVG = []
        SVGElements = self.getSVGElements(bar)
        for SVGElement in SVGElements:
            elementsWithSVG.extend(self.getElementsWithSVGElement(SVGElement))
        for e in elementsWithSVG:
            if self.elementHasRole(e, self.SyntacticRoles.METRIC_BAR):
                subElements.append(e)
        return subElements

    def getStackedBarOfMetric(self, bar):
        """
        Returns the parent stacked bar of the given metric bar, if it exists
        :param bar: string; name of a metric bar instance
        :return: string; name of the parent stacked bar instance; None if not found
        """
        parent = None
        if self.elementHasRole(bar, self.SyntacticRoles.METRIC_BAR):
            containers = self.getContainerElements(bar)
            for e in containers:
                if self.elementHasRole(e, self.SyntacticRoles.STACKED_BAR):
                    parent = e
                    break
        return parent

    def getBarLineups(self):
        """
        Returns bar instance names grouped by their lineups
        @return dict<string, list<string>> Keys are lineup instance names, values are lists of bar instance names
        belonging to the lineup
        """
        return self.elementsInRelation(self.O2OGraphicRelation.ORDERED_LINEUP, [self.SyntacticRoles.METRIC_BAR,
                                                                                self.SyntacticRoles.STACKED_BAR])

    def pathBetweenBars(self, bar_start=None, bar_end=None, bars=None):
        """
        Return the bars that have to be visited between two bars, following their navigational order
        :param bar_start: bar instance name where the path begins; None to start from the beginning
        :param bar_end: bar instance name where the path ends; None to end in the last bar
        :param bars: bars to consider; None for all
        :return: list<string> list of bar instances from bar_start to bar_end
        """
        if bars is None:
            bars = self.getBars()
        orderedBars = self.getBarsOrders(bars)
        ordered_path = []
        if orderedBars:
            start_found = bar_start is None
            reverse = False
            for t in sorted(orderedBars.items(), key=orderedBars.get):
                if t[1]:
                    if not start_found:
                        if t[1] == bar_start:
                            start_found = True
                        elif t[1] == bar_end:
                            reverse = True
                            start_found = True
                            bar_end = bar_start
                    if start_found:
                        ordered_path.append(t[1])
                        if t[1] == bar_end:
                            break
            if reverse:
                ordered_path = ordered_path[::-1]
        return ordered_path

    def applyLowLevelTask(self, task, **kwargs):
        """
        Applies a low level-task from the Chart Task Ontology on the current
        chart
        @task: the name of the low-level task
        @kwargs: the named parameters required by the task
        @return: The output of the given task, usually a bar subset
        """
        if task == self.StructuralTask.ReadingTask.APPLY_QFILTER:
            filters = kwargs['filters'] if 'filters' in kwargs else None
            return self.filterBars(filters)
        elif task == self.StructuralTask.ReadingTask.FILTER:
            filters = kwargs['filters'] if 'filters' in kwargs else None
            operator = kwargs['operator'] if 'operator' in kwargs else None
            operand = kwargs['operand'] if 'operand' in kwargs else None
            negate = kwargs['negate'] if 'negate' in kwargs else False
            barset = kwargs['barset'] if 'barset' in kwargs else None
            return self.filterBarsWithValues(filters, operator, operand,
                                             negate, barset)
        elif task == self.StructuralTask.ComparisonTask.COMPUTE_DERIVED_VAL:
            op = kwargs['operator'] if 'operator' in kwargs else None
            barset = kwargs['barset'] if 'barset' in kwargs else []
            return self.computeDerived(op, barset)
        elif task == self.StructuralTask.ComparisonTask.FIND_EXTREMUM or \
             task == self.StructuralTask.ComparisonTask.RANGE:
            ops = ['min', 'max']
            barset = kwargs['barset'] if 'barset' in kwargs else []
            info = self.computeExtreme(ops, barset)
            return info

    def filterBars(self, query_filters):
        """
        Filter chart bars according to the given QueryFilter instances
        :param query_filters: list<QueryFilter>
        :return: list<string> bar instance URIs
        """
        labels = {}  # {Textual label: negate}
        user_tags = {}  # {User tag to filter: negate}
        values = []  # Bars values to filter
        cardinal_f_result = []  # Cardinal Filters applied to result
        cardinal_f_label = []  # Cardinal Filters applied to labels
        for f in query_filters:
            if isinstance(f, QueryFilterNominal):
                for o in f.operands:
                    if f.is_user_label:
                        user_tags[o] = f.negate
                    elif f.is_axis_value:
                        values.append(float(o))
                    else:
                        labels[o] = f.negate
            elif isinstance(f, QueryFilterCardinal):
                if f.result:
                    cardinal_f_result.append(f)
                elif f.property and f.property.OE.uri == "%s#%s" % (self.VIS_NS, self.SyntacticProperty.IS_LABELED_BY):
                    cardinal_f_label.append(f)
        # Apply nominal filters first
        pos_labels = []
        neg_labels = []
        for l, n in labels.iteritems():
            if n:
                neg_labels.append(l)
            else:
                pos_labels.append(l)
        bars = set(self.getMetricBars() + self.getStackedBars())
        if pos_labels:
            bars = self.__filterBarsWithFilters(pos_labels, negate=False, barset=bars)
        if neg_labels:
            bars = self.__filterBarsWithFilters(neg_labels, negate=True, barset=bars)
        if not bars:
            return []
        # Apply user tag filters
        pos_labels = []
        neg_labels = []
        for l, n in user_tags.iteritems():
            if n:
                neg_labels.append(l)
            else:
                pos_labels.append(l)
        if pos_labels:
            bars = self.__filterBarsWithFilters(pos_labels, negate=False, user_tags=True, barset=bars)
        if neg_labels:
            bars = self.__filterBarsWithFilters(neg_labels, negate=True, user_tags= True, barset=bars)
        if not bars:
            return []
        to_remove = set()
        n_bars = len(bars)
        i = 0
        for b in bars:
            added = False
            b_v = self.getMetricBarValue(b)
            for v in values:
                if v != b_v:
                    to_remove.add(b)
                    added = True
            if not added:
                for f in cardinal_f_result:
                    if not f.assertFilter(b_v):
                        to_remove.add(b)
            if added:
                i += 1
                if i == n_bars:
                    break
        bars = bars - to_remove
        if cardinal_f_label:
            for b in bars:
                bar_filters = [f for f in self.getElementFilters(b, returnText=True) if isNumber(f)]
                if bar_filters:
                    for f in cardinal_f_label:
                        if all(not f.assertFilter(b_label) for b_label in bar_filters):
                            to_remove.add(b)
        return list(bars - to_remove)

    def computeExtreme(self, ops, bars, n=1):
        """
        Retrieves data cases possessing an extreme value of an attribute over
        its range within the data set: maximum, minimum of bars' values
        :param list<string> ops: A list of operations or a single operation
         e.g. max, min
        :param set<string> bars: the bars whose values to take into account
        :param n: int; maximum number of tied elements to return, or 'all' to return all tied elements
        :return dict<string, list<(string, float)>>. Key: op, value: list of (bar name, value)
        e.g. {'max' : [('bar123', 1000)], 'min' : [('bar456', 10), ('bar789', 10)]}
        """
        if not isinstance(ops, list):
            ops = [ops]
        # (name, value) pairs of bars
        barVals = {}
        result = {}
        for bar in bars:
            v = self.getMetricBarValue(bar)
            if v:
                barVals[bar] = float(v)
        if len(barVals) > 0:
            if 'max' in ops:
                result['max'] = []
            if 'min' in ops:
                result['min'] = []
            max_v = float("-inf")
            min_v = float("inf")
            for b, v in barVals.iteritems():
                if v > max_v:
                    result['max'] = [(b, v)]
                    max_v = v
                elif v == max_v:
                    result['max'].append((b, v))
                if v < min_v:
                    result['min'] = [(b, v)]
                    min_v = v
                elif v == min_v:
                    result['min'].append((b, v))
            if isNumber(n) and n > 0:
                result['max'] = result['max'][: n]
                result['min'] = result['min'][: n]
            result['range'] = (None, result['max'][0][1] - result['min'][0][1])  # Range value only, no bar name
        return result

    def computeDerived(self, op, bars):
        """
        Returns the result of a derived value operation on a set of bars
        @param string op: the name of the operation to perform (avg, median, mode, count)
        @param iterable<string> bars: the bars whose values to take into
        account
        @return float: the result of the derived operation
        """
        from collections import defaultdict
        derived = None
        totalVal = 0.0
        countbars = 0
        maxVal = float_info.min
        minVal = float_info.max
        bar_vals = []
        val_occurrences = defaultdict(int)
        for bar in bars:
            barVal = float(self.getMetricBarValue(bar))
            val_occurrences[barVal] += 1
            bar_vals.append(barVal)
            totalVal += barVal
            countbars += 1
            if barVal > maxVal:
                maxVal = barVal
            if barVal < minVal:
                minVal = barVal
        if countbars <= 0:
            derived = None
        else:
            if op == 'avg':
                derived = totalVal / float(countbars)
            elif op == 'median':
                vals_sorted = sorted(bar_vals)
                i = countbars / 2
                if countbars % 2 == 0:
                    derived = (vals_sorted[i] + vals_sorted[i-1]) / 2.0
                else:
                    derived = vals_sorted[i]
            elif op == 'mode':
                derived = max(val_occurrences, key=val_occurrences.get)
            elif op == 'count':
                derived = countbars
            elif op == 'sum':
                derived = totalVal
        return derived

    def computeCompare(self, bars):
        """
        Compares the current and home bar, if any, with the given bars.
        :param bars: list<string>; bars to take into account
        :return: (string, boolean): NL answer of the task and whether the task could be completed
        """
        from config import MAX_OUTPUT_NODES
        answer = ''
        success = False
        if bars:
            units = ''
            chart_units = self.getChartMeasurementUnit()
            if chart_units:
                units = "%s " % chart_units.replace("_", " ").lower()
            to_compare = []
            current = self.getCurrentBar()
            if current:
                to_compare.append('current')
            home = self.getHomeNodes()
            if home:
                to_compare.append('home')
            if to_compare:
                n_bars = len(bars)
                ordered_bars = self.sortBarsAccordingToNavigation(bars[:MAX_OUTPUT_NODES])
                for c_label in to_compare:
                    if c_label == 'current':
                        curr_filters = self.getElementFiltersString(current)
                    elif c_label == 'home':
                        curr_filters = self.getElementFiltersString(home[0])
                    else:
                        break
                    answer += '<h5>%s bar %s\'s value is:</h5>' % (c_label.capitalize(), curr_filters)
                    answer += '<section><ul>'
                    for b in ordered_bars:
                        if c_label == 'current':
                            if b == current:
                                continue
                            val_diff, rel_diff = self.compareBars(current, b)
                        elif c_label == 'home':
                            if b == home[0]:
                                continue
                            val_diff, rel_diff = self.compareBars(home[0], b)
                        else:
                            val_diff, rel_diff = None, None
                        labels = self.getElementFiltersString(b, add_brackets=False)
                        if val_diff is not None:
                            if abs(rel_diff) >= 5:
                                cmp = 'more' if val_diff > 0 else 'less'
                                answer += '<li>%s: %s %s%s (%.2f%%)</li>' % (labels, abs(val_diff), units, cmp,
                                                                             rel_diff)
                            elif abs(rel_diff) >= 2:
                                answer += "<li>%s: almost the same</li>" % labels
                            else:
                                answer += "<li>%s: the same</li>" % labels
                            success = True
                    if n_bars > MAX_OUTPUT_NODES:
                        n_skipped = n_bars - MAX_OUTPUT_NODES
                        answer += "<li>Too many elements to show. %d elements have been skipped.</li>" % n_skipped
                    answer += '</ul></section>'
        return answer, success

    def sortBars(self, bars, descending=True):
        """
        Sorts the given bars in the given order according to their values
        :param iterable<string> bars: bars to take into account
        :param descending: boolean: whether to return the bars in descending (default) or descending order
        :return: dict(string, float): Sorted bars and their values
        """
        import operator
        bar_vals = {}
        for b in bars:
            val = self.getMetricBarValue(b)
            if val:
                bar_vals[b] = val
        sorted_b = sorted(bar_vals.items(), key=operator.itemgetter(1), reverse=descending)
        return sorted_b

    def sortBarsAccordingToNavigation(self, bars):
        """
        Returns the given bars as sorted in the order given by their navigation
        :param bars: list<string> bars to consider
        :return: list<string> sorted bars
        """
        sorted_b = []
        bars_nav = self.getBarsOrders(bars)
        if bars_nav:
            sorted_b = [bars_nav[v] for v in sorted(bars_nav)]
        else:  # Default sort: stacked bar followed by its metric bars
            for b in bars:
                if self.elementHasRole(b, self.SyntacticRoles.STACKED_BAR):
                    sorted_b.append(b)
                    sorted_b.extend([m for m in self.getMetricBarsOfStacked(b) if m in bars])
            sorted_b.extend([b for b in bars if b not in sorted_b])  # Add leftover bars
        return sorted_b

    def getBarValues(self, bars):
        """
        Return the values of the given bar graphic objects
        :param bars: list<string> bars to consider
        :return: dict<string; float>: keys are bar ids, values are bar values
        """
        vals = {}
        for bar in bars:
            vals[bar] = float(self.getMetricBarValue(bar))
        return vals

    def computeSort(self, bars, descending=True):
        """
        Returns the result of a sort analytical task
        :param iterable<string> bars: bars to take into account
        :param descending: boolean: whether to return the bars in descending (default) or descending order
        :return: string; task answer
        """
        from config import MAX_OUTPUT_NODES
        answer = ''
        sorted_b = self.sortBars(bars, descending)
        if sorted_b:
            answer += "<h5>Sorted %d bars :</h5>" % len(sorted_b)
            units = self.getChartMeasurementUnit()
            if units:
                units_answer = ' %s' % units
            else:
                units_answer = ''
            i = 0
            answer += '<section><ul>'
            sorted_b_truncated = sorted_b[:MAX_OUTPUT_NODES]
            for b, v in sorted_b_truncated:
                i += 1
                answer += "<li>%s bar %s: %s%s</li>" % (numberToOrdinal(i), self.getElementFiltersString(b), v,
                                                        units_answer)
            if len(sorted_b) > MAX_OUTPUT_NODES:
                answer += '<li>And %d more (not shown)</li>' % (len(sorted_b) - MAX_OUTPUT_NODES)
            answer += '</ul></section>'
        else:
            answer = 'No bars found'
        return answer

    def computeDistribution(self, bars):
        """
        Returns the result of a distribution characterization task on a set of bars
        @param iterable<string> bars: the bars whose values to take into account
        @return (string, boolean): task answer, and whether the task could be resolved
        """
        success = False
        answer = 'The answer could not be computed'
        try:
            from stats.DataAnalyzer import DataAnalyzer
            if bars:
                bar_vals = self.getBarValues(bars)
                if bar_vals:
                    analyzer = DataAnalyzer(bar_vals)
                    dist, params = analyzer.dist_best_fit()
                    if dist:
                        d_label = analyzer.dist_to_string(dist, params)
                        answer = 'The data for these bars best fits a %s' % d_label
                        success = True
                    else:
                        answer = 'The distribution could not be characterized'
        except ImportError:
            answer = 'Task (characterize distribution) not supported!'
        finally:
            return answer, success

    def computeClustering(self, bars):
        """
        Returns the result of a clustering task on a set of bars according to their values
        @param iterable<string> bars: the bars whose values to take into account
        @return (string, boolean): task answer, and whether the task could be resolved
        """
        from config import MAX_OUTPUT_NODES
        success = False
        answer = 'The answer could not be computed'
        try:
            from stats.DataAnalyzer import DataAnalyzer
            bar_vals = self.getBarValues(bars)
            if not bar_vals:
                return answer
            analyzer = DataAnalyzer(bar_vals)
            clusters, outliers = analyzer.find_clusters()
            n_clusters = len(clusters)
            if n_clusters > 1:
                units = self.getChartMeasurementUnit()
                if units:
                    units_label = units.replace("_", " ").lower()
                else:
                    units_label = ''
                answer = "<h5>Found %d possible bar groupings:</h5>" % n_clusters
                answer += '<section><ul>'
                for i, c in enumerate(clusters, 1):
                    common_labels = set()
                    cluster = c[:MAX_OUTPUT_NODES]
                    answer += "<li><strong>%s cluster" % (numberToOrdinal(i))
                    ul_html = '<ul>'
                    for j, bar in enumerate(cluster):
                        str_l, labels = self.printBarDetails(bar, skipNav=True, units=units_label)
                        ul_html += '<li>%s</li>' % str_l
                        if j == 0:
                            common_labels |= labels
                        else:
                            common_labels &= labels
                    n_c = len(c)
                    if n_c > MAX_OUTPUT_NODES:
                        ul_html += '<li>And %d more</li>' % (n_c - MAX_OUTPUT_NODES)
                    ul_html += "</ul></li>"
                    if common_labels:
                        answer += ' (%s)' % ", ".join(common_labels)
                    answer += "</strong>:%s" % ul_html
                answer += '</ul></section>'
                if outliers:
                    common_labels = set()
                    ul_html = '<section><ul>'
                    outliers_trimmed = outliers[:MAX_OUTPUT_NODES]
                    for j, bar in enumerate(outliers_trimmed):
                        str_l, labels = self.printBarDetails(bar, skipNav=True, units=units_label)
                        ul_html += '<li>%s</li>' % str_l
                        if j == 0:
                            common_labels |= labels
                        else:
                            common_labels &= labels
                    n_o = len(outliers)
                    if n_o > MAX_OUTPUT_NODES:
                        ul_html += '<li>And %d more</li>' % (n_o - MAX_OUTPUT_NODES)
                    ul_html += '</ul></section>'
                    c_l = ''
                    if common_labels:
                        c_l = ' (%s)' % ", ".join(common_labels)
                    answer += "<h5>The remaining bars%s do not belong to any group:</h5>" % c_l
                    answer += ul_html
                success = True
            else:
                answer = 'The bars of your query could not be grouped! Try with a broader query'
        except ImportError:
            answer = 'Task (clustering) not supported!'
        finally:
            return answer, success

    def computeFindAnomalies(self, bars):
        """
        Returns the result of the task of finding anomalies on the given set of bars according to their values
        @param iterable<string> bars: the bars whose values to take into account
        @return (string, boolean): task answer, and whether the task could be resolved
        """
        from config import MAX_OUTPUT_NODES
        success = False
        answer = 'The answer could not be computed'
        try:
            from stats.DataAnalyzer import DataAnalyzer
            if bars:
                bar_vals = self.getBarValues(bars)
                if bar_vals:
                    analyzer = DataAnalyzer(bar_vals)
                    _, outliers = analyzer.find_clusters()
                    if outliers:
                        units = self.getChartMeasurementUnit()
                        if units:
                            units_label = units.replace("_", " ").lower()
                        else:
                            units_label = ''
                        n_o = len(outliers)
                        ul_html = '<section><ul>'
                        outliers_trimmed = outliers[:MAX_OUTPUT_NODES]
                        common_labels = set()
                        for i, bar in enumerate(outliers_trimmed, 1):
                            bar_info, labels = self.printBarDetails(bar, skipNav=True, units=units_label)
                            ul_html += "<li><strong>%s bar:</strong> %s</li>" % (numberToOrdinal(i), bar_info)
                            if i == 0:
                                common_labels |= labels
                            else:
                                common_labels &= labels
                        if n_o > MAX_OUTPUT_NODES:
                            ul_html += '<li>And %d more</li>' % (n_o - MAX_OUTPUT_NODES)
                        ul_html += '</ul></section>'
                        c_str = ''
                        if common_labels:
                            c_str = replaceLastCommaWithAnd(' (with shared labels: %s)' % ", ".join(common_labels))
                        answer = "<h5>Found %d possible bar outliers%s:</h5>" % (n_o, c_str)
                        answer += ul_html
                        success = True
                    else:
                        answer = 'No anomalies found within the bars of this chart.'
        except ImportError:
            answer = 'Task (find anomalies) not supported!'
        finally:
            return answer, success

    def computeBarsNavOrder(self):
        """
        Initializes the datatype properties specifying navigation bar order
        according to their coordinates with respect to the category axis
        """
        barsCoors = {}
        stacked = self.getStackedBars()
        metric = self.getMetricBars()
        metricAxis = self.getMetricAxis()
        o = self.getOrientation(metricAxis)
        #  Coordinate to order bars is the opposite of metric axis orientation
        if o == self.VisualAttribute.Spatial.Orientation.VERTICAL_ORIENTATION:
            coorMod = 1
            coorProp = self.SytacticDataProperty.HAS_X_COOR
        elif o == self.VisualAttribute.Spatial.Orientation.HORIZONTAL_ORIENTATION:
            coorMod = -1 # y-coordinate goes from top to bottom; invert it
            coorProp = self.SytacticDataProperty.HAS_Y_COOR
        else:
            raise Exception("Axis orientation (%s) not supported" % o)

        if len(stacked) > 0:
            checkChildren = True
            for b in stacked:
                barsCoors[b] = self.getValue(b, coorProp) * coorMod
        else:
            checkChildren = False
            for b in metric:
                barsCoors[b] = self.getValue(b, coorProp) * coorMod
        #  List of sorted bars from smaller to higher coordinate
        barsSorted = sorted(barsCoors, key=lambda k: float(barsCoors[k]))
        currentSet = False
        n = 0
        for i, bar in enumerate(barsSorted):
            n += 1
            if not currentSet:
                currentSet = True
                self.setCurrentBar(bar)
            self.__addBarOrder(bar, n)
            if checkChildren:
                for childBar in self.getMetricBarsOfStacked(bar):
                    n += 1
                    self.__addBarOrder(childBar, n)
        return None

    def __addBarOrder(self, bar, n):
        """
        Adds an order datatype property to the given bar for user navigation
        @param bar: an instance name of a metric or stacked bar
        @param n: and integer specifying the order of the bar in the graph
        """
        if bar and n:
            self.removeDataTypePropertyTriple(bar, self.NavigationDataProperty.HAS_ORDER)
            self.addDataTypePropertyTriple(bar, self.NavigationDataProperty.HAS_ORDER, n, XSD.int, functional=True)

    def __filterBarsWithFilters(self, filters, negate=False, user_tags=False, barset=None):
        """
        Returns the bars that satisfy the given filters (i.e. are tagged by ALL the labels given, including
        navigation properties)
        :param filters: list<string>; a list or set of textual filters (i.e. labels' text)
        :param negate: boolean; whether to logically negate the results (default False)
        :param user_tags: boolean; whether the filter must be compared (only) to the bars' user tags. If false,
        filters are compared to the bar's labels in the diagram
        :param barset: a set with the bars to take into account; None (default) for all
        :return set<string>: bar element names that satisfy the filters
        """
        if not barset:
            barset = set(self.getMetricBars() + self.getStackedBars())
        if filters is not None:
            filters_set = set(filters)
            labelsSet = filters_set.copy()
            for f in filters_set:
                navFilter = True
                if f == self.NavigationEntity.HOME_NODE:
                     barset &= set(self.getHomeNodes())
                elif f == self.NavigationEntity.CURRENT_NODE:
                    barset &= set(self.getCurrentBar())
                elif f == self.NavigationEntity.LAST_NODE:
                    barset &= set(self.getPreviousNodes())
                else:
                    navFilter = False
                if navFilter:
                    labelsSet.remove(f)
            if user_tags:
                barset &= set(self.getElementsWithUserLabels(labelsSet, negate))
            else:
                for bar_filter in labelsSet:
                    elements_labeled = set(self.getElementsLabeledByText(bar_filter))
                    if negate:
                        barset -= elements_labeled
                    else:
                        barset &= elements_labeled
        return barset

    def getCurrentBar(self):
        """
        Return the instance name of the currently selected bar
        :return string: instance name of current bar in the ontology
        """
        current = self.getCurrentNodes()
        if len(current) > 1:
            raise NavigationException("More than one current bar selected!")
        elif len(current) == 0:
            return None
        else:
            bar = current[0]
        if not self.elementHasRole(bar, self.SyntacticRoles.METRIC_BAR) and \
           not self.elementHasRole(bar, self.SyntacticRoles.STACKED_BAR):
            raise NavigationException("Current element '%s' is not a bar!" % bar)
        return bar

    def setCurrentBar(self, newCurrent):
        """
        Sets the given bar as the current one
        @param newCurrent: the instance name of the new current bar
        """
        self.setCurrentNodes([newCurrent])

    def computeJumpToBar(self, bar):
        """
        Jumps to the given bar, if possible, and returns a NL description of the way
        :param bar; string (bar instance name) or list of bar instance names.
        :return: string; description of the jump. None if action cannot be taken.
        """
        output = None
        if isinstance(bar, list):
            if len(bar) > 1:  # If there is only one stacked bar in the list, jump to it
                goto_bar = None
                for b in bar:
                    if self.elementHasRole(b, self.SyntacticRoles.STACKED_BAR):
                        if goto_bar:  # Second stacked bar found -> jump not possible
                            goto_bar = None
                            break
                        else:
                            goto_bar = b
                if goto_bar:
                    bar = goto_bar
                else:
                    return 'You cannot jump to more than one bar at the same time! Your query has returned %d bars' \
                           % len(bar)
            elif bar:
                bar = bar[0]
        if isinstance(bar, basestring):
            path = self.__moveToBar(bar, default_curr_first=False)
            if path:
                output = 'Jumped from '
                output += self.printBarDetails(path[0], skipNav=True)[0]
                output += '<br/>to: '
                output += self.printPath(path, skipNav=True)
        return output

    def __setCurrentAsHome(self):
        """
        Set the current bar as the home node and delete all previous home node
        properties from the ontology
        @return string: instance name of new home node (current bar)
        """
        cur = [self.getCurrentBar()]
        if cur:
            self.setHomeNodes(cur)
        return cur

    def __goToHome(self):
        """
        Sets the current bar as the one having the IS_HOME_NODE property as True
        :return list<string>: single-item list with the name of the new current bar (home node)
        """
        h = self.getHomeNodes()
        if len(h) > 1:
            raise NavigationException("More than one home node selected!")
        elif len(h) == 0:
            return [None]
        else:
            return self.__moveToBar(h[0], default_curr_first=False)

    def resetNavigation(self):
        """
        Reset the navigation, i.e. reset bar orders and current bar, and move
        to the first bar. Can be also used to initialize graph navigation
        predicates.
        @return string: instance name of first bar
        """
        super(BarChartOntology, self).resetNavigation()
        self.computeBarsNavOrder()
        axis = self.getMetricAxis()
        if axis:
            self.computeAxisLengthFromLabels(axis)
        self.reasonLabelsFromLegends()
        return self.__moveFirst()

    def __getExtremeNavBar(self, pos='first', bars=None):
        """
        Return the first or last bar of the chart
        :param pos: string; 'first' or 'last'
        :param bars; list<string> bar instance names to consider; None for all
        :return string: instance name of first or last bar
        """
        b = None
        if bars is None:
            stacked_bars = self.getStackedBars()
            if len(stacked_bars) == 0:
                bars = None  # None defaults to all bars in getBarsOrders
            else:
                bars = stacked_bars
        orderedBars = self.getBarsOrders(bars)
        if len(orderedBars) > 0:
            if pos == 'first':
                i = min(orderedBars, key=int)
            else:
                i = max(orderedBars, key=int)
            b = orderedBars[i]
        elif bars:
            b = bars[0]  # Fallback to any bar
            from warnings import warn
            warn('getExtremeNavBar: bars are not ordered, random bar fetched.')
        return b

    def __getFirst(self):
        """
        Return the first bar of the chart
        :return string: instance name of first bar
        """
        return self.__getExtremeNavBar('first')

    def __getLast(self):
        """
        Return the last bar of the chart
        :return string: instance name of last bar
        """
        return self.__getExtremeNavBar('last')

    def __moveFirst(self):
        """
        Set the first stacked bar contained as the current one. If the are none,
        set the first metric bar
        :return list<string>: list containing the instance name of first bar or None
        """
        ordered_path = []
        first = self.__getFirst()
        if first:
            ordered_path = self.__moveToBar(first, bars=None, default_curr_first=False)
        return ordered_path

    def __moveLast(self):
        """
        Set the last stacked bar as the current one. If the are none, set the last metric bar
        :return list<string>: instance names of all bars from the current one until the last bar
        """
        ordered_path = []
        next = self.__getLast()
        if next:
            ordered_path = self.__moveToBar(next)
        return ordered_path

    def __moveToBar(self, bar, bars=None, default_curr_first=True):
        """
        Set the given bar as the current one and return the path from the current bar to it.
        :param bar: string; bar instance name the user is moving to
        :param bars: list<string>; bars to consider, None to infer automatically
        :param prior_stacked: boolean; whether to prioritize stacked bar instances if they exist
        :param default_curr_first: boolean; whether to use first bar as current bar if it does not exist
        :return: list<string>: instance names of all bars from the current one until the given bar
        """
        ordered_path = []
        current = self.getCurrentBar()
        bar_role = None
        if self.elementHasRole(bar, self.SyntacticRoles.STACKED_BAR):
            bar_role = self.SyntacticRoles.STACKED_BAR
        elif self.elementHasRole(bar, self.SyntacticRoles.METRIC_BAR):
            bar_role = self.SyntacticRoles.METRIC_BAR
        next = None
        if not current and default_curr_first:
            current = self.__getFirst()
        if current:
            cur_role = None
            if self.elementHasRole(current, self.SyntacticRoles.STACKED_BAR):
                cur_role = self.SyntacticRoles.STACKED_BAR
            elif self.elementHasRole(current, self.SyntacticRoles.METRIC_BAR):
                cur_role = self.SyntacticRoles.METRIC_BAR
            cont = True
            use_stacked = False
            if bar_role == self.SyntacticRoles.STACKED_BAR:
                use_stacked = True
                if cur_role == self.SyntacticRoles.METRIC_BAR:
                    current = self.getStackedBarOfMetric(current)
            elif cur_role == self.SyntacticRoles.STACKED_BAR:
                cont = False
            if cont:
                if use_stacked:
                    all_bars = self.getStackedBars()
                else:
                    all_bars = self.getMetricBars()
                if bars:
                    nav_bars = list(set(bars) & set(all_bars))
                else:
                    nav_bars = all_bars
                ordered_path = self.pathBetweenBars(bar_start=current, bar_end=bar, bars=nav_bars)
                next = ordered_path[-1] if ordered_path else None
        if not ordered_path and bar:
            if current:
                ordered_path.append(current)
            next = bar
            ordered_path.append(next)
        if next:
            self.setCurrentBar(next)
        return ordered_path

    def __moveDown(self):
        """
        Set the first metric bar contained in the current stacked bar as the current one, if possible
        :return list<string>: instance names of the current and child bars
        """
        path_bars = []
        candidates = []
        current = self.getCurrentBar()
        if current:
            path_bars.append(current)
            if self.elementHasRole(current, self.SyntacticRoles.STACKED_BAR):
                children = self.getConstituentElements(current)
                for e in children:
                    if self.elementHasRole(e, self.SyntacticRoles.METRIC_BAR):
                        candidates.append(e)
                ordered = self.getBarsOrders(candidates)
                minOrder = min(ordered, key=int)
                next = ordered[minOrder]
                self.setCurrentBar(next)
                path_bars.append(next)
        return path_bars

    def __moveUp(self):
        """
        Set the stacked bar the current one belongs to as the current bar, if possible
        :return list<string>: instance names of the current and parent bars
        """
        path_bars = []
        current = self.getCurrentBar()
        if current:
            path_bars.append(current)
            if self.elementHasRole(current, self.SyntacticRoles.METRIC_BAR):
                parent = self.getStackedBarOfMetric(current)
                if parent:
                    self.setCurrentBar(parent)
                    path_bars.append(parent)
        return path_bars

    def __moveNext(self, bars=None):
        """
        Set the next bar as the current one, as given by their order properties
        :param bars: bar instance names to take into account; None for all indexed by their ordinal values
        :return list<string>: instance names of the current and next bars
        """
        return self.__horizontalStep(bars, 1)

    def __movePrev(self, bars=None):
        """
        Set the previous bar as the current one, as given by their order properties
        :param bars: bar instance names to take into account; None for all
        :return list<string>: instance names of the current and previous bars
        """
        return self.__horizontalStep(bars, -1)

    def __horizontalStep(self, bars=None, n=1):
        """
        Set the next bar as the n-th next or previous one, as given by the bars' order property
        :param bars: bar instance names to take into account; None for all
        :param n: int; number of steps. If n is negative, steps are taken
        to the left (previous bars), otherwise to the right
        :return list<string>: instance names of all bars from the current one until the goal bar after having taken
        n steps in the given direction
        """
        current = self.getCurrentBar()
        path_bars = [current]
        if n != 0:
            barsOrder = self.getBarsOrders(bars)
            v = self.getValue(current, self.NavigationDataProperty.HAS_ORDER)
            if v:
                curr_n = int(v)
                curr_role = self.getRolesOfElement(current)
            else:
                raise NavigationException("Current bar %s has no ordinal value!" % current)
            i = curr_n
            if n > 0:
                stop_i = max(barsOrder, key=int)
            else:
                stop_i = min(barsOrder, key=int)
            found = False
            c = 0  # bar counter to skip the previous n-1 bars
            while not found:
                i += 1 if n > 0 else -1
                if i in barsOrder:
                    next = barsOrder[i]
                    next_role = self.getRolesOfElement(next)
                    mbr = self.SyntacticRoles.METRIC_BAR
                    sbr = self.SyntacticRoles.STACKED_BAR
                    if (mbr in curr_role and mbr in next_role) or (sbr in curr_role and sbr in next_role):
                        c = c + 1
                        path_bars.append(next)
                        if c == abs(n):
                            found = True
                            self.setCurrentBar(next)
                if (n > 0 and i > stop_i) or (n < 0 and i < stop_i):
                    found = True
        return path_bars

    def __moveExtreme(self, op, bars=None):
        """
        Set the bar with the given extreme value as the current one
        :param op: string; 'max' or 'min' to consider the bar with the highest or lowest value, respectively.
        :param bars: set of bars to take into account
        :return: list<string>: instance names of all bars from the current one until the highest bar
        """
        path_bars = []
        if op in ['max', 'min']:
            current = self.getCurrentBar()
            if not current:
                current = self.__getFirst()
            if current:
                if bars is None:
                    bars = self.getStackedBars()
                    if not bars:
                        bars = self.getBars()
                extremes = self.computeExtreme(op, bars)
                max_bar, _ = extremes[op][0]
                self.setCurrentBar(max_bar)
                if self.elementHasRole(current, self.SyntacticRoles.METRIC_BAR) and \
                        self.elementHasRole(max_bar, self.SyntacticRoles.STACKED_BAR):
                    current = self.getStackedBarOfMetric(current)
                path_bars = self.pathBetweenBars(current, max_bar, bars)
        return path_bars

    def __moveHighest(self, bars=None):
        """
        Set the bar with the highest value as the current one
        @param bars: set of bars to take into account
        :return list<string>: instance names of all bars from the current one until the highest bar
        """
        return self.__moveExtreme('max', bars)

    def __moveLowest(self, bars=None):
        """
        Set the bar with the lowest value as the current one
        @param bars: set of bars to take into account
        @return string: instance name of the next bar
        """
        return self.__moveExtreme('min', bars)

    def filterBarsForTask(self, bars, task_sc):
        """
        Filter the given bars; in some tasks, if there are stacked bars among them return only the stacked bars
        :param bars: list<string>: bar instance names
        :param task_sc: SemanticConcept; analytical task instance
        :return: list<string> filtered bars
        """
        task = self.stripNamespace(task_sc.task)
        tasks_prior_stacked = [self.StructuralTask.DerivedValueTask.AVERAGE,
                               self.StructuralTask.DerivedValueTask.MODE,
                               self.StructuralTask.DerivedValueTask.MEDIAN,
                               self.StructuralTask.DerivedValueTask.SUM,
                               self.StructuralTask.DerivedValueTask.COUNT,
                               self.StructuralTask.CorrelationTask.CLUSTER]
        filtered_bars = []
        if task in tasks_prior_stacked:
            filtered_bars = [b for b in bars if self.elementHasRole(b, self.SyntacticRoles.STACKED_BAR)]
        return filtered_bars if filtered_bars else bars

    def getCurrentBarUserTags(self):
        """
        Fetches the user-defined tags of the current bar
        @return string: the user-defined label of the current bar, 'No Tags'
        string if not found.
        """
        bar = self.getCurrentBar()
        ulbls = self.getUserLabels(bar)
        if not ulbls:
            ulbls = "No Tags"
        return ulbls

    def barPoints(self, bars):
        """
        Return the topmost point of each given bar as given by their coordinates
        :param bars: list<string>; bar instances to consider
        :return: list<(float, float)>: x and y coordinates of points in the 2D plane; y starts from top of canvas
        """
        points = []
        for b in bars:
            x, y = self.getCoordinate(b, 'x'), self.getCoordinate(b, 'y')  # Coordinates at bar center
            top_y = y - self.lengthOfElement(b) / 2.0  # y coordinate at top of the bar
            points.append((x, top_y))
        return points

    def printPath(self, bars, skipNav=False, target='prev', units=None):
        """
        Prints information about a navigational path between the given bars
        :param bars: list<string>: a list of bars that have been navigated in the given order
        :param skipNav: boolean; whether to skip user navigation information
        :param target: string; what the current bar is being compared against: the previously visited bar ('prev'),
        or the home bar ('home')
        :param units: string; units to print after each bar. None to infer from ontology
        :return: string; path information in NL
        """
        path = ''
        add_units = True
        if units is None:
            chart_units = self.getChartMeasurementUnit()
            if chart_units:
                units = chart_units.replace("_", " ").lower()
            else:
                add_units = False
        n_bars = len(bars)
        if n_bars > 0:
            path = self.printBarDetails(bars[-1], skipNav, units)[0]
        if n_bars > 1:
            path += "<br/>"
            if target == 'prev':
                t_str = 'the previously visited bar'
            elif target == 'home':
                t_str = 'the home bar'
            else:
                t_str = 'the other bar'
            val_diff, rel_diff = self.compareBars(bars[-1], bars[0])
            v = abs(val_diff)
            r = abs(rel_diff)
            u = "%s " % units if add_units else ''
            if val_diff > 0:
                cmp_str = "higher"
            else:
                cmp_str = "lower"
            show_trend = self.trendIsMeaningful(bars)
            if n_bars == 2 and abs(rel_diff) <= 2.0:
                path += "It has a similar value to %s." % t_str
            else:
                if n_bars == 2:
                    if show_trend:
                        points = self.barPoints(bars)
                        trend = self.straightSlopeLabel(points)
                        path += "There is a %s between this bar and %s" % (trend, t_str)
                        path += "; its value is %.2f %s(%.2f%%) %s." % (v, u, r, cmp_str)
                    else:
                        path += "This bar's value is %.2f %s(%.2f%%) %s than %s." % (v, u, r, cmp_str, t_str)
                else:
                    n_between = n_bars - 2
                    n_verb = 'are' if n_between > 1 else 'is'
                    n_pl = 's' if n_between > 1 else ''
                    if show_trend:
                        points = self.barPoints(bars)
                        path += "There %s %d bar%s between this bar and %s. " % (n_verb, n_between, n_pl, t_str)
                        trend = self.straightSlopeLabel(points)
                        path += "The bars follow a %s" % trend
                        path += "<br/>"
                    path += "The current bar's value is %.2f %s(%.2f%%) %s than %s' value." % (v, u, r, cmp_str, t_str)
        return path

    def trendIsMeaningful(self, path, max_n=50):
        """
        Returns whether the trend on a given path between bars should be displayed
        :param path: list<string>; a sorted list of bar instance names specifying a path from path[0] to path [-1]
        :param max_n: int; maximum number of bars to consider, if higher then skip trend display
        :return: boolean; whether the trend information of the path is meaningful and should be given to the user
        """
        show_trend = False
        n_elements = len(path)
        if 2 <= n_elements <= max_n:
            if self.getElementsWithRole(self.SyntacticRoles.STACKED_BAR):
                if self.elementHasRole(path[-1], self.SyntacticRoles.STACKED_BAR) and \
                        self.elementHasRole(path[0], self.SyntacticRoles.STACKED_BAR):
                    show_trend = True
            else:
                show_trend = True  # No stacked bars in the diagram
        return show_trend

    def compareBars(self, bar_focus, bar_other):
        """
        Compare the given bars
        :param bar_focus: string; bar instance being compared
        :param bar_other: string; bar instance to compare against the main bar
        :return: (float, float: Absolute difference and relative difference (%) between the bars' values
        """
        other_val = float(self.getMetricBarValue(bar_other))
        return self.compareBarToVal(bar_focus, other_val)

    def compareBarToVal(self, bar, val):
        """
        Compare the given bar to the given value
        :param bar: string; bar instance being compared
        :param val: float; numeric value to compare the bar's value against
        :return: (float, float: Absolute difference and relative difference (%) between the bar and the value
        """
        val_diff, rel_diff = None, None
        if val is not None and bar:
            bar_val = float(self.getMetricBarValue(bar))
            if bar_val is not None:
                val_diff = bar_val - val
                rel_diff = -(1 - bar_val / val) * 100
        return round(val_diff, 2), round(rel_diff, 2)

    def printCompareValToHome(self, val):
        """
        Compares the given value to the value of the home bar and prints it
        :param val: float; a numeric value; usually the result of a derived task
        :return: string; natural-language comparison between the given value and the home bar
        """
        label = ''
        home_nodes = self.getHomeNodes()
        if len(home_nodes) == 1 and val is not None:
            home = home_nodes[0]
            home_val = float(self.getMetricBarValue(home))
            if home_val is not None:
                label = 'The result is '
                rel_diff = -(1 - val / home_val) * 100
                cmp_str = ''
                if abs(rel_diff) < 5:
                    label += 'almost the same to home bar\'s value'
                elif rel_diff < 0:
                    cmp_str = 'smaller'
                else:
                    cmp_str = 'bigger'
                if cmp_str:
                    label += '%.2f%% %s than the home bar\'s value' % (abs(rel_diff), cmp_str)
        return label

    def printCompareBars(self, bar_focus, bar_other, target='prev', units=None):
        """
        Print a comparison between the values of the given bars
        :param bar_focus: string; bar instance being compared
        :param bar_other: string; bar instance to compare against the main bar
        :param target: string; what the current bar is being compared against: the previously visited bar ('prev'),
        or the home bar ('home')
        :param units: string; units to print after each bar. None to infer from ontology
        :return: string; natural-language comparison between the bars
        """
        val_diff, rel_diff = self.compareBars(bar_focus, bar_other)
        add_units = True
        if units is None:
            chart_units = self.getChartMeasurementUnit()
            if chart_units:
                units = chart_units.replace("_", " ").lower()
            else:
                add_units = False
        if target == 'prev':
            t_str = 'the previously visited bar'
        elif target == 'home':
            t_str = 'the home bar'
        else:
            t_str = 'the other bar'
        v = abs(val_diff)
        r = abs(rel_diff)
        u = "%s " % units if add_units else ''
        if val_diff > 0:
            cmp_str = "higher"
        else:
            cmp_str = "lower"
        label = "The current bar's value is %.2f %s(%.2f%%) %s than %s' value." % (v, u, r, cmp_str, t_str)
        return label

    def printCompareToHome(self, bar):
        """
        Prints a comparison between the given bar and the home bar, if any
        :param bar: string; bar instance
        :return: string; natural language comparison between the bars
        """
        out = ''
        home = self.getHomeNodes()
        if len(home) == 1:
            out = self.printCompareBars(bar, home[0], 'home')
        return out

    def printBarDetails(self, bar, skipNav=False, units=None):
        """
        Print a natural-language description of a bar's information, including:
            - Whether it is a simple (metric) or a stacked bar
            - Its textual labels
            - Its value according to the size in relation to the metric axis
            - Its units according to the chart's metric axis
            - Its current user navigation properties, if skipNav is set to False
            - Its user-defined labels
        :param bar: string; a bar instance name
        :param skipNav: boolean; whether to skip user navigation information
               (i.e. if the bar is the current or home bar)
        :param units: string; units to print after each bar. None to infer from ontology
        :return (string, set): a natural-language description of the bar and a set with its labels
        """
        output = ''
        if bar:
            if units is not None:
                unitsNL = units
            else:
                units = self.getChartMeasurementUnit()
                if units:
                    unitsNL = units.replace("_", " ").lower()
                else:
                    unitsNL = "(units unknown)"
            barfilters = set(str(v) for v in self.getElementFilters(bar) if v)
            if self.elementHasRole(bar, self.SyntacticRoles.STACKED_BAR):
                output += "Stacked bar "
            else:
                output += "Simple bar "
            if len(barfilters) > 0:
                output += 'with labels: '
                output += ', '.join(sorted([f for f in barfilters]))
            size = self.getMetricBarValue(bar)
            if isinstance(size, int):
                output += " (%d %s). " % (size, unitsNL)
            else:
                output += " (%0.2f %s). " % (size, unitsNL)
            navFilters = self.getNavigationProperties(bar)
            for nf in navFilters:
                if not skipNav:
                    if nf == self.NavigationDataProperty.IS_CURRENT:
                        output += "This is the current bar. "
                if nf == self.NavigationDataProperty.IS_HOME_NODE:
                    output += "This is the home bar. "
                if nf == self.NavigationDataProperty.HAS_USER_LABEL:
                    ul = navFilters[nf]
                    output += "User tags: %s. " % ul
        else:
            output += "Bar not found!"
        return output, barfilters

    def __printLabels(self, element):
        """
        Returns a print-ready string with the labels of the given element
        @param element: the name of an ontology element
        @retun string: a comma-separated list of labels that apply to the elem
        """
        if element:
            tags = ",".join([f for f in self.getElementFilters(element) if f])
        else:
            tags = ""
        return tags
