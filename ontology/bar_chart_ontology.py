from ontology.upper_vis_ontology import UpperVisOntology
from NLP.model.QueryFilter import QueryFilterCardinal, QueryFilterNominal
from sys import float_info
from rdflib import XSD
from GeneralUtil import isNumber, stringOpToPython


class BarChartOntology(UpperVisOntology):
    """
    Bar Chart Ontology handler; subclass of Upper Visualization Ontology for handling bar charts
    """
    def __init__(self, RDFPath):
        """
        BarChartOntology constructor
        :param RDFpath: string; path to an RDF ontology file
        """
        super(BarChartOntology, self).__init__(RDFPath)

    class BarChartProperty:
        """Object properties related to bar charts"""
        HAS_TOP_LABEL = "has_top_label"
        HAS_BOTTOM_LABEL = "has_bottom_label"

    def getStackedBars(self):
        """
        Returns the stacked bars in the chart
        @return: A lits of stacked bar instance names
        """
        return self.getElementsWithRole(self.SyntacticRoles.STACKED_BAR)

    def navigate(self, actions, bars = None):
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
        of the results might be None when no result is available and should
        be handled properly.
        """
        outputbars = []
        for action in actions:
            b = None
            if action == self.StructuralTask.NavigationTask.WHERE:
                b = self.getCurrentBar()
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
            outputbars.append(b)
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

        # Bar line-ups. In simple (ungrouped) bar charts there is only one
        lineups = self.getBarLineups()
        lcount = len(lineups)
        if lcount > 1:
            output += ("The chart has its bars grouped into %d subsets:<br/>"
                                                                    % lcount)
        allLabels = set(self.getLabels())

        for l, bars in lineups.iteritems():
            # Try to find the common label of the lineup
            labels = allLabels.copy()
            # Bar individual labels (excluding labels common to all the bars
            # in the lineup)
            specificLabels = {}
            stacked = []
            simple = []
            for b in bars:
                barLabels = self.getElementFilters(b, returnText=False)
                labels &= barLabels
                specificLabels[b] = barLabels
            for b in bars:
                #Remove common labels to the lineup
                specificLabels[b] = specificLabels[b] - labels
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
                output += " Mean of stacked bars: %.2f %s<br/>" \
                            % (stackedMean, units)
            # Navigate through stacked bars and output averages
            output += "This subset (%s) is further divided into:<br/>" \
                        % lbloutput
            for b in stacked:
                specificLblTxt = [self.getText(l) for l in specificLabels[b]]
                output += ",".join(specificLblTxt) + "<br/>"

        output += "Extreme values of graph:<br/>"

        extremeMetric = self.computeExtreme(['max', 'min'], self.getMetricBars())
        extremeStacked = self.computeExtreme(['max', 'min'], self.getStackedBars())
        bar, value = extremeStacked['max']
        tags = ",".join([f for f in self.getElementFilters(bar) if f])
        output += "Stacked bars maximum: %.2f (tags: %s)<br/>" \
            % (value, tags)
        bar, value = extremeStacked['min']
        tags = ",".join([f for f in self.getElementFilters(bar) if f])
        output += "Stacked bars minimum: %.2f (tags: %s)<br/>" \
            % (value, tags)
        bar, value = extremeMetric['max']
        tags = ",".join([f for f in self.getElementFilters(bar) if f])
        output += "Metric bars maximum: %.2f (tags: %s)<br/>" \
            % (value, tags)
        bar, value = extremeMetric['min']
        tags = ",".join([f for f in self.getElementFilters(bar) if f])
        output += "Metric bars minimum: %.2f (tags: %s)<br/>" \
            % (value, tags)

        output += "End of summary.<br/>"
        return output

    def getChartTitle(self):
        """
        Returns the title of the whole chart
        @return sting: The title (or titles concatenated with commas), None
        if not found
        """
        chart = self.getInstances(
                          self.PrimaryGraphicRepresentation.STATISTICAL_CHART)
        if chart:
            # A chart is labeled by its title
            lbls = set(self.getLabelsOfElement(chart[0]))
            titles = ", ".join([self.getText(l) for l in lbls if l])
            if titles:
                return titles
        return None

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
        barset = self.__filterBarsWithFilters(filters, negate, barset)
        op = stringOpToPython(op, negate)
        if operand is not None and op:
            filtered = set()
            for bar in barset:
                l = self.getMetricBarValue(bar)
                if op(l, float(operand)):
                    filtered.add(bar)
            return filtered
        elif operand is None:
            return barset
        else:
            raise Exception("Filter: operator '%s' not supported" % op)

    def getElementFilters(self, element, returnText = True):
        """
        Retrieves the filters that apply to an element given by its labels,
        color and other attributes
        @param element: the name of a metric bar instance
        @param returnText: whether to return the text of the labels (True) or
        the instance names of the label elements (False)
        @return set<sting>: a list of the texts of those labels that apply
        to the bar if returText is True, or a list of label instance names
        otherwise
        """
        labels = set(self.getLabelsOfElement(element))
        color = self.getValue(element, self.SyntacticProperty.HAS_COLOR)
        if color:  # TODO: retrieve filters according to other attributes
            legends = self.getLegends()
            for legend in legends:
                legendElements = self.getLegendPairs(legend)
                for subelement, label in legendElements:
                    elementColor = self.getValue(subelement,
                                         self.SyntacticProperty.HAS_COLOR)
                    if elementColor == color:
                        """Add label from legend to the bar"""
                        self.addObjectPropertyTriple(subelement,
                                            self.SyntacticProperty.IS_LABELED_BY,
                                            label)
                        labels.add(label)
        if returnText:
             # Discard NoneType and ""
            return set([self.getText(l) for l in labels if l])
        else:
            return set([l for l in labels if l])

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

    def getLegends(self):
        """
        Returns the legends of the chart
        @return List<string>: a list of element names
        """
        return self.getElementsWithRole(self.InformationalRoles.LEGEND_OBJECT,
                                        "informational")

    def getLegendPairs(self, legend):
        """
        Retrieves the pairs of informational objects and their labels that
        appear on a given legend
        @param legend: the name of a Legend instance
        @return list<(string, string)>: a list of (object, label) instance names
        """
        pairs = set()
        if legend:
            elementsOfLegend = self.getConstituentElements(legend)
            for e in elementsOfLegend:
                if self.elementHasRole(e, self.SyntacticRoles.LABEL):
                    labeled = self.getSubjects(self.SyntacticProperty.IS_LABELED_BY,
                                               e)
                    for l in labeled:
                        if l in elementsOfLegend:
                            pairs.add((l, e))
        return list(pairs)

    def getLegendsDescription(self):
        """
        Returns a description of the chart's legends and their sub-elements
        @return string: a natural language enumeration of the legends' labels
        """
        legends = self.getLegends()
        output = "This chart has "
        n = len(legends)
        if n == 0:
            output += "no legends.<br/>"
        else:
            if n > 1:
                output += "more than "
            output += "one legend. "
        for i, legend in enumerate(legends, start=1):
            if n > 1:
                output += "Legend number %d has the following items:<br/>" % i
            else:
                output += "The legend is made up of the following items: "
            pairs = self.getLegendPairs(legend)
            output += ", ".join([self.getText(l)
                                 for s,l in self.getLegendPairs(legend)])
            output += "<br/>"
        return output

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
            axisLength = self.lengthOfAxis(axis)
            (topl, bottoml) = self.getExtremeLabels(axis)
            if not topl:
                raise Exception("Axis not correctly labeled: top label not found.")
        else:
            raise Exception("Axis not found in chart.")

        length = self.lengthOfElement(metricBar)
        if axisLength > 0 and length > 0:
            bottomval = float(self.getText(bottoml)) if bottoml else 0
            topval = float(self.getText(topl))
            value = bottomval + ((topval * length) / axisLength)

        return value

    def lengthOfElement(self, element):
        """
        Returns the length of a given element as returned by its has_length
        datatype property.
        @param element: the name of an instance in the ontology
        @return float: the length of the element, -1 if not found
        """
        length = -1.0
        if element:
            if self.elementHasRole(element, self.SyntacticRoles.STACKED_BAR):
                l = self.lengthOfStackedBar(element)
            else:
                l = self.getValue(element, self.SytacticDataProperty.HAS_LENGTH)
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
            self.addDataTypePropertyTriple(element,
                                           self.SytacticDataProperty.HAS_LENGTH,
                                           length,
                                           datatype = XSD.float
                                           )
        else:
            length = float(l)
        return length

    def getMetricBarsOfStacked(self, bar):
        """
        Returns the metric sub-bars that make up a given stacked bar
        @param bar: the name of a stacked bar instance
        @return list<string>: a list of metric bar instances
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

    def getChartMeasurementUnit(self):
        """
        Returns the units the chart is concerned about (if it has only one axis)
        @return: string: a measurement unit
        """
        axis = self.getMetricAxis()
        return self.getMetricAxisMeasurementUnit(axis)

    def getMetricAxis(self):
        """
        Returns the metric axis of the chart (usually the vertical one)
        @return string: the name of the metric axis element
        """
        axisList = self.getElementsWithRole(self.SyntacticRoles.AXIS)
        for axis in axisList:
            if self.elementHasRole(axis,
                               self.InformationalRoles.SPATIAL_REFERENCE_OBJECT,
                               "informational"):
                return axis
        return None

    def getMetricAxisMeasurementUnit(self, axis):
        """
        Returns the measurement units of a given metric axis
        @param axis: the name of the axis
        @return string: the name of the measurement unit as given by the
                expresses_cardinal_information property
        """
        if axis:
            cardinalInfo = self.getObjects(axis, self.StatisticalProperty.
                                           EXPRESSES_CARDINAL_INFORMATION)
            if cardinalInfo:
                if len(cardinalInfo) == 1:
                    units = cardinalInfo[0].lower().replace("_", " ")
                    return units
                else:
                    raise Exception(("Axis %s is associated "
                                    "with more than one cardinal "
                                    "information.") % axis)

    def getMetricAxisTitle(self, axis):
        """
        Looks for a non-numerical label of the given axis and returns it
        @param axis: the name of the axis individual
        @return string: the title of the axis, None if not found
        """
        title = None
        labels = self.labelsOfAxis(axis)
        for l in labels:
            lText = self.getText(l)
            if lText and not isNumber(lText):
                title = lText
        return title

    def getAxisDescription(self):
        """
        Returns a description of the chart's axes and their labels
        @return string: a natural language enumeration of the axes
        """
        output = ""
        metricAxis = self.getMetricAxis()
        if metricAxis:
            orientation = self.getOrientation(metricAxis)
            axisTitle = self.getMetricAxisTitle(metricAxis)
            if axisTitle:
                output = "The metric axis has the title \"%s\". " % axisTitle
            else:
                output = "The metric axis has no title. "
            if orientation:
                output += "It has %s." % orientation.replace('_', ' ').lower()
            output += "<br/>"
        else:
            output = "This chart has no metric axis<br/>"
        return output

    def labelsOfAxis(self, axis):
        """
        Returns the labels existing along the given axis
        @param axis: the name of the axis
        @return list<string> a list of label elements' names
        """
        if axis:
            labels = self.getObjects(axis, self.SyntacticProperty.
                                           IS_LABELED_BY)
            return labels

    def getExtremeLabels(self, axis):
        """
        Returns the topmost and bottom-most labels of a vertical axis
        @param axis: the name of the axis
        @return (string, string): a tuple containing the names of the top label
        (smallest Y-axis value) and the bottom label (greatest Y-axis value)
        """
        topLabel = None
        bottomLabel = None
        if axis:
            topLabel = self.getValue(axis, self.BarChartProperty.HAS_TOP_LABEL)
            bottomLabel = self.getValue(axis, self.BarChartProperty.HAS_BOTTOM_LABEL)
        return (str(topLabel), str(bottomLabel))

    def lengthOfAxis(self, axis):
        """
        Returns the length of a given labeled axis. If the axis length can not
        be retrieved, computes and saves it
        @param axis: the name of the axis
        @return int: the length in pixels of the axis as given by the position
        of its labels in the Y axis
        """
        length = 0
        if axis:
            length = self.lengthOfElement(axis)
            if length <= 0:
                labels = self.labelsOfAxis(axis)
                topLabel = None
                bottomLabel = None
                """Top and bottom are inverted in SVG i.e. the topmost Y
                   coordinate has the lowest value """
                topYCoor = float_info.max
                bottomYCoor = float_info.min
                for label in labels:
                    lText = self.getText(label)
                    if lText and isNumber(lText):
                        y = self.getCoordinate(label, coor="y")
                        if y:
                            if y < topYCoor:
                                topYCoor = y
                                topLabel = label
                            if y > bottomYCoor:
                                bottomYCoor = y
                                bottomLabel = label
                if topLabel and bottomLabel:
                    length = bottomYCoor - topYCoor
                    self.addDataTypePropertyTriple(axis,
                                                   self.SytacticDataProperty.HAS_LENGTH,
                                                   length, datatype = XSD.float)
                    self.addObjectPropertyTriple(axis,
                                                self.BarChartProperty.HAS_TOP_LABEL,
                                                topLabel)
                    self.addObjectPropertyTriple(axis,
                                                self.BarChartProperty.HAS_BOTTOM_LABEL,
                                                bottomLabel)

        return length

    def getIndependentVariables(self):
        """
        Returns the name of the classes representing Independent Variables in
        the ontology
        @return list<string>: names of the independent variables
        """
        return self.getSubclasses(self.StatisticalVarType.INDEPENDENT_VARIABLE)

    def getBarLineups(self):
        """
        Returns bar instance names grouped by their lineups
        @return dict<string, list<string>> Keys are lineup instance names, values are lists of bar instance names
        belonging to the lineup
        """
        return self.elementsInRelation(self.O2OGraphicRelation.ORDERED_LINEUP, [self.SyntacticRoles.METRIC_BAR,
                                                                                self.SyntacticRoles.STACKED_BAR])

    def applyAnalyticalTask(self, task_sc, bars):
        """
        Apply an analytical task to the given bars
        :param task_sc: SemanticConcept instance with the task
        :param bars: list<string> bars to which the task will be applied
        :return: string; answer in NL
        """
        answer = ''
        task = self.stripNamespace(task_sc.task)
        if task == self.StructuralTask.DerivedValueTask.AVERAGE:
            avg = self.computeDerived('avg', bars)
            units = self.getChartMeasurementUnit()
            answer = 'Average is %.2f' % float(avg)
            if units:
                answer += ' %s' % units
        if answer:
            answer += '<br/>'
        return answer

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
        cardinal_f_result = []  # Cardinal Filters applied to result
        cardinal_f_label = []  # Cardinal Filters applied to labels
        for f in query_filters:
            if isinstance(f, QueryFilterNominal):
                for o in f.operands:
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
        to_remove = set()
        if bars:
            for f in cardinal_f_result:
                for o in f.operands:
                    bars = self.filterBarsWithValues(filters=None, op=f.opToPython(), operand=o,
                                                     negate=f.negate, barset=bars)
                    if not bars:
                        break
            if cardinal_f_label:
                for b in bars:
                    bar_filters = [f for f in self.getElementFilters(b, returnText=True) if isNumber(f)]
                    if bar_filters:
                        for f in cardinal_f_label:
                            op = stringOpToPython(f.opToPython(), f.negate)
                            for b_f in bar_filters:
                                for o in f.operands:
                                    if not op(b_f, o):
                                        to_remove.add(b)
        return list(bars - to_remove)

    def computeExtreme(self, ops, bars):
        """
        Retrieves data cases possessing an extreme value of an attribute over
        its range within the data set: maximum, minimum of bars' values
        @param list<string> ops: A list of operations or a single operation
         e.g. max, min
        @param set<string> bars: the bars whose values to take into account
        @return dict<string, (string, float)>. Key: op, value: (bar name, value)
        e.g. {'max' : ('bar123', 1000), 'min' : ('bar456', 10)}
        """
        if not isinstance(ops, list):
            ops = [ops]
        # (name, value) pairs of bars
        barVals = {}
        result = {}
        for bar in bars:
            v = self.getMetricBarValue(bar)
            if v:
                barVals[bar] = v
        if len(barVals) > 0:
            maxBar = max(barVals, key=barVals.get)
            minBar = min(barVals, key=barVals.get)
            if 'max' in ops:
                result['max'] = (maxBar, barVals[maxBar])
            if 'min' in ops:
                result['min'] = (minBar, barVals[minBar])
             # Add a tuple without an associated bar, only the range value
            result['range'] = (None, barVals[maxBar] - barVals[minBar])
        return result

    def computeDerived(self, op, bars):
        """
        Returns the result of a derived value operation on a set of bars
        @param string op: the name of the operation to perform
        @param iterable<string> bars: the bars whose values to take into
        account
        @return float: the result of the derived operation
        """
        derived = None
        totalVal = 0.0
        countbars = 0
        countSimple = 0
        maxVal = float_info.min
        minVal = float_info.max
        minSimple = float_info.max
        for bar in bars:
            barVal = self.getMetricBarValue(bar)
            if op == 'avg':
                totalVal += barVal
                countbars += 1
                if barVal > maxVal:
                    maxVal = barVal
                if barVal < minVal:
                    minVal = barVal
        if op == 'avg':
            if countbars > 0:
                derived = totalVal / float(countbars)
        return derived

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
        #Coordinate to order bars is the opposite of metric axis orientation
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
        #List of sorted bars from smaller to higher coordinate
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
            self.removeDataTypePropertyTriple(
                                              bar,
                                              self.NavigationDataProperty.HAS_ORDER
                                              )
            self.addDataTypePropertyTriple(
                               bar,
                               self.NavigationDataProperty.HAS_ORDER,
                               n,
                               XSD.int
                               )

    def __filterBarsWithFilters(self, filters, negate = False, barset = None):
        """
        Returns the bars that satisfy the given filters (i.e. are tagged by ALL
        the labels given, including navigation properties)
        @param filters: a list or set of textual filters (i.e. labels' text)
        @param negate: whether to logically negate the results (default False)
        @param barset: a set with the bars to take into account;
               None (default) for all
        @return set<string>: bar element names that satisfy the filters
        """
        if not barset:
            barset = set(self.getMetricBars() + self.getStackedBars())
        if filters is not None:
            barsOut = set()
            filtersSet = set([self.normalizeItem(f) for f in filters])
            labelsSet = filtersSet.copy()
            for f in filtersSet:
                navFilter = True
                if f == self.NavigationEntity.HOME_NODE:
                     barset &= set(self.getHomeNodes())
                elif f == self.NavigationEntity.CURRENT_NODE:
                    barset &= set([self.getCurrentBar()])
                elif f == self.NavigationEntity.LAST_NODE:
                    barset &= set(self.getPreviousNodes())
                else:
                    navFilter = False
                if navFilter:
                    labelsSet.remove(f)
            for bar in barset:
                barFilters = self.getElementFilters(bar)
                if labelsSet.issubset(barFilters):
                    if not negate:
                        barsOut.add(bar)
                else:
                    if negate:
                        barsOut.add(bar)
        else:
            barsOut = barset
        return barsOut

    def getCurrentBar(self):
        """
        Return the instance name of the currently selected bar
        @return string: instance name of current bar in the ontology
        """
        current = self.getCurrentNodes()
        if len(current) > 1:
            raise Exception("More than one current bar selected!")
        elif len(current) == 0:
            return None
        else:
            bar = current[0]
        if not self.elementHasRole(bar, self.SyntacticRoles.METRIC_BAR) and \
           not self.elementHasRole(bar, self.SyntacticRoles.STACKED_BAR):
            raise Exception("Current element '%s' is not a bar!" % bar)
        return bar

    def setCurrentBar(self, newCurrent):
        """
        Sets the given bar as the current one
        @param newCurrent: the instance name of the new current bar
        """
        self.setCurrentNodes([newCurrent])

    def __setCurrentAsHome(self):
        """
        Set the current bar as the home node and delete all previous home node
        properties from the ontology
        @return string: instance name of new home node (current bar)
        """
        cur = self.getCurrentBar()
        if cur:
            self.setHomeNodes([cur])
        return cur

    def __goToHome(self):
        """
        Sets the current bar as the one having the IS_HOME_NODE property as True
        @return string: the name of the new current bar (home node)
        """
        h = self.getHomeNodes()
        if len(h) > 1:
            raise Exception("More than one home node selected!")
        elif len(h) == 0:
            return None
        else:
            bar = h[0]
            self.setCurrentBar(bar)
            return bar

    def resetNavigation(self):
        """
        Reset the navigation, i.e. reset bar orders and current bar, and move
        to the first bar. Can be also used to initialize graph navigation
        predicates.
        @return string: instance name of first bar
        """
        super(BarChartOntology, self).resetNavigation()
        self.computeBarsNavOrder()
        return self.__moveFirst()

    def __moveFirst(self):
        """
        Set the first stacked bar contained as the current one. If the are none,
        set the first metric bar
        @return string: instance name of first bar
        """
        next = None
        bars = self.getStackedBars()
        if len(bars) == 0:
            bars = None
        orderedBars = self.getBarsOrders(bars)
        if len(orderedBars) > 0:
            minOrder = min(orderedBars, key=int)
            next = orderedBars[minOrder]
            self.setCurrentBar(next)
        return next

    def __moveLast(self):
        """
        Set the last stacked bar contained as the current one. If the are none,
        set the last metric bar
        @return string: instance name of last bar
        """
        next = None
        bars = self.getStackedBars()
        if len(bars) == 0:
            bars = None
        orderedBars = self.getBarsOrders(bars)
        if len(orderedBars) > 0:
            maxOrder = max(orderedBars, key=int)
            next = orderedBars[maxOrder]
            self.setCurrentBar(next)
        return next

    def __moveDown(self):
        """
        Set the first metric bar contained in the current stacked bar as
        the current one, if possible
        @return string: instance name of next bar
        """
        next = None
        candidates = []
        current = self.getCurrentBar()
        if self.elementHasRole(current, self.SyntacticRoles.STACKED_BAR):
            children = self.getConstituentElements(current)
            for e in children:
                if self.elementHasRole(e, self.SyntacticRoles.METRIC_BAR):
                    candidates.append(e)
            ordered = self.getBarsOrders(candidates)
            minOrder = min(ordered, key=int)
            next = ordered[minOrder]
            self.setCurrentBar(next)
        return next

    def __moveUp(self):
        """
        Set the stacked bar the current one belongs to as the current bar, if
        possible
        @return string: instance name of next bar
        """
        next = None
        current = self.getCurrentBar()
        if self.elementHasRole(current, self.SyntacticRoles.METRIC_BAR):
            containers = self.getContainerElements(current)
            for e in containers:
                if self.elementHasRole(e, self.SyntacticRoles.STACKED_BAR):
                    next = e
                    self.setCurrentBar(e)
                    break
        return next

    def __moveNext(self, bars = None):
        """
        Set the next bar as the current one, as given by their order properties
        @param bars: bar instance names to take into account; None for all
        indexed by their ordinal values
        @return string: instance name of next bar with respect to the current
        one
        """
        return self.__horizontalStep(bars, 1)

    def __movePrev(self, bars = None):
        """
        Set the previous bar as the current one, as given by their order
        properties
        @param bars: bar instance names to take into account; None for all
        @return string: instance name of previous bar with respect to the
        current one
        """
        return self.__horizontalStep(bars, -1)

    def __horizontalStep(self, bars = None, n = 1):
        """
        Set the next bar as the n-th next or previous one, as given by the bars'
        order property
        @param bars: bar instance names to take into account; None for all
        @param int n: number of steps. If n is negative, steps are taken
        to the left (previous bars), otherwise to the right
        @return string: instance name of the next bar with respect to the
        current one after taking n horizontal steps in either direction
        """
        next = None
        barsOrder = self.getBarsOrders(bars)
        if n != 0:
            current = self.getCurrentBar()
            v = self.getValue(current, self.NavigationDataProperty.HAS_ORDER)
            if v:
                curr_n = int(v)
                curr_role = self.getRolesOfElement(current)
            else:
                raise Exception("Current bar %s has no ordinal value!" % current)
            i = curr_n
            if n > 0:
                stop_i = max(barsOrder, key=int)
            else:
                stop_i = min(barsOrder, key=int)
            found = False
            c = 0 # bar counter to skip the previous n-1 bars
            while not found:
                i += 1 if n > 0 else -1
                if i in barsOrder:
                    next = barsOrder[i]
                    next_role = self.getRolesOfElement(next)
                    if (self.SyntacticRoles.METRIC_BAR in curr_role or
                        (self.SyntacticRoles.STACKED_BAR in curr_role and
                        self.SyntacticRoles.STACKED_BAR in next_role)):
                            c = c + 1
                            if c == abs(n):
                                found = True
                                self.setCurrentBar(next)
                if (n > 0 and i > stop_i) or (n < 0 and i < stop_i):
                    next = None
                    found = True
        return next

    def __moveHighest(self, bars=None):
        """
        Set the bar with the highest value as the current one
        @param bars: set of bars to take into account
        @return string: instance name of the next bar
        """
        barName = None
        if bars is None:
            bars = self.getStackedBars()
            if not bars:
                bars = self.getBars()
        extremes = self.computeExtreme('max', bars)
        (barName, barVal) = extremes['max']
        self.setCurrentBar(barName)
        return barName

    def __moveLowest(self, bars=None):
        """
        Set the bar with the lowest value as the current one
        @param bars: set of bars to take into account
        @return string: instance name of the next bar
        """
        barName = None
        if bars is None:
            bars = self.getStackedBars()
            if not bars:
                bars = self.getBars()
        extremes = self.computeExtreme('min', bars)
        (barName, barVal) = extremes['min']
        self.setCurrentBar(barName)
        return barName

    def getCurrentBarUserTags(self):
        """
        Fetches the user-defined tags of the current bar
        @return string: the user-defined label of the current bar, 'No Tags'
        string if not found.
        """
        bar = self.getCurrentBar()
        ulbls = self.getUserLabels(bar)
        if not ulbls:
            ulbls = "<No Tags>"
        return ulbls

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
