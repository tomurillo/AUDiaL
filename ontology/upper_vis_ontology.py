from flask import session
from sys import float_info
from ontology.upper_ontology import UpperOntology
from NLP.util.TreeUtil import quick_norm
import rdflib
from rdflib import XSD, URIRef
from collections import defaultdict
import const as c
from general_util import isNumber


class UpperVisOntology(UpperOntology):
    """
    Upper Visualization Ontology handler
    """
    def __init__(self, RDFPath, sess_id='', reload=False):
        """
        UpperVisOntology constructor
        :param RDFpath: string; path to an RDF ontology file
        :param sess_id: string; session ID to use as prefix for session attributes
        :param reload: bool; whether to re-fetch ontology data from the given file
        """
        super(UpperVisOntology, self).__init__(RDFPath, sess_id, reload)
        #  Abbreviations of entities e.g. used as suffixes in entity names
        self.ENTITY_ABBRV = {"GO": self.SyntacticEntity.GRAPHIC_OBJECT,
                             "GR": self.SyntacticEntity.GRAPHIC_RELATION,
                             "GS": self.SyntacticEntity.GRAPHIC_SPACE,
                             "IR": self.SyntacticEntity.INFORMATIONAL_ROLE,
                             "SR": self.SyntacticEntity.SYNTACTIC_ROLE,
                             "VA": self.SyntacticEntity.VISUAL_ATTRIBUTE
                             }
        self.SYNT_ENTS = [attr for attr in dir(self.SyntacticEntity())
                          if not callable(attr) and not attr.startswith("__")]
        self.SYNT_ROLES = [attr for attr in dir(self.SyntacticRoles())
                           if not callable(attr) and not attr.startswith("__")]
        self.NAV_PROP = [attr for attr in dir(self.NavigationDataProperty())
                         if not callable(attr) and not attr.startswith("__")]

    class SyntacticEntity:
        """
        Enum-like class containing upper visualization ontology classes
        """
        CORRESPONDENCE = "Correspondence"
        GRAPHIC_OBJECT = "Graphic_Object"
        COMPOSITE_GO = "Composite_GO"
        COMPOSITE_GRAPHIC_OBJECT = "Composite_GO"
        ELEMENTARY_GO = "Elementary_GO"
        ELEMENTARY_GRAPHIC_OBJECT = "Elementary_GO"
        COMPOSITE_SYMBOL = "Composite_Symbol"
        GRAPHIC_RELATION = "Graphic_Relation"
        GRAPHIC_SPACE = "Graphic_Space"
        INFORMATIONAL_ROLE = "Informational_Role"
        SYNTACTIC_ROLE = "Syntactic_Role"
        VISUAL_ATTRIBUTE = "Visual_Attribute"
        NONE = "None"

    class NavigationEntity:
        HOME_NODE = "Home_Node"
        LAST_NODE = "Last_Node"
        CURRENT_NODE = "Current_Node"

    class PrimaryGraphicRepresentation:
        GROUPING_DIAGRAM = "Grouping_Diagram_GR"
        LINK_DIAGRAM = "Link_Diagram_GR"
        MAP = "Map_GR"
        PHOTOGRAPH = "Photograph_GR"
        PICTURE = "Picture_GR"
        STATISTICAL_CHART = "Statistical_Chart_GR"
        SYMBOL = "Symbol_GR"
        TABLE = "Table_GR"
        TIME_CHART = "Time_Chart_GR"
        WRITTEN_TEXT = "Written_Text_GR"

    class O2OGraphicRelation:
        """
        Object-to-Object graphic relations
        """
        CLUSTERING = "Clustering_GR"
        CONTAINMENT = "Containment_GR"
        LABELLING = "Labelling_GR"
        LINEUP = "Lineup_GR"
        ORDERED_LINEUP = "Ordered_Lineup_GR"
        PROP_REPETITION = "Proportional_Repetition_GR"
        LINKING = "Linking_GR"
        SEPARATION = "Separation_By_Separator_GR"
        SUPERIMPOSITION = "Superimposition_GR"

    class SyntacticProperty:
        """
        Upper visualization ontology object properties
        """
        HAS_SYNTACTIC_ROLE = "has_syntactic_role"
        IS_SYNTACTIC_ROLE_OF = "is_syntactic_role_of"
        HAS_INFORMATIONAL_ROLE = "has_informational_role"
        IS_LABELED_BY = "is_labeled_by"
        IS_LABEL_FOR = "is_label_for"
        HAS_COLOR = "has_color_named"
        HAS_ORIENTATION = "has_orientation_named"
        HAS_DATATYPE = "has_datatype"

    class StatisticalProperty:
        """
        Object properties related to statistical elements
        """
        EXPRESSES_INFORMATION = "expresses_information"
        EXPRESSES_CARDINAL_INFORMATION = "expresses_cardinal_information"
        EXPRESSES_NOMINAL_INFORMATION = "expresses_nominal_information"
        EXPRESSES_ORDINAL_INFORMATION = "expresses_ordinal_information"

    class NavigationObjectProperty:
        """
        Object Properties that aid with navigation
        """
        HAS_PREVIOUS = "has_previous_node"
        HAS_NEXT = "has_next_node"

    class NavigationDataProperty:
        """
        Datatype Properties that aid with navigation
        """
        HAS_ORDER = "hasOrder"
        IS_CURRENT = "isCurrentNode"
        IS_HOME_NODE = "isHomeNode"
        IS_PREVIOUS_VISITED = "isPreviousVisitedNode"
        HAS_USER_LABEL = "has_user_label"  # User-defined element label
        HAS_SPECIFICITY = "has_specificity"
        HAS_DISTANCE_SCORE = "has_distance_score"
        HAS_PROP_FINAL_SCORE = "has_property_final_score"

    class SytacticDataProperty:
        """
        Upper visualization ontology datatype properties
        """
        HAS_Y_COOR = "hasYCoordinate"
        HAS_X_COOR = "hasXCoordinate"
        HAS_TEXT = "has_text"
        HAS_SVG_ELM = "hasSVGElement"
        HAS_LENGTH = "has_length"

    class SyntacticRoles:
        """Upper visualization syntactic role members"""
        AXIS = "Axis_SR"
        CONTAINER = "Container_SR"
        DIRECTED_CONNECTOR = "Directed_Connector_SR"
        GRID_LINE = "Grid_Line_SR"
        LABEL = "Label_SR"
        LINE_LOCATOR = "Line_Locator_SR"
        METRIC_BAR = "Metric_Bar_SR"
        MODIFIER = "Modifier_SR"
        NODE = "Node_SR"
        POINT_LOCATOR = "Point_Locator_SR"
        SEPARATOR = "Separator_SR"
        STACKED_BAR = "Stacked_Bar_SR"
        SURFACE_LOCATOR = "Surface_Locator_SR"
        UNDIRECTED_CONNECTOR = "Undirected_Connector_SR"

    class MetricAxisProperty:
        HAS_TOP_LABEL = "has_top_label"
        HAS_BOTTOM_LABEL = "has_bottom_label"

    class InformationalRoles:
        DECORATION_OBJECT = "Decoration_Object"
        INFORMATION_OBJECT = "Information_Object"
        LEGEND_OBJECT = "Legend_Reference_Object_IR"
        SPATIAL_REFERENCE_OBJECT = "Spatial_Reference_Object_IR"

    class StatisticalVarType:
        DEPENDENT_VARIABLE = "Dependent_Variable"
        INDEPENDENT_VARIABLE = "Independent_Variable"

    class VisualAttribute:
        class Spatial:
            class Orientation:
                VERTICAL_ORIENTATION = "Vertical_Orientation"
                HORIZONTAL_ORIENTATION = "Horizontal_Orientation"
                DIAGONAL_LEFT_ORIENTATION = "Diagonal_Left_Orientation"
                DIAGONAL_RIGHT_ORIENTATION = "Diagonal_Right_Orientation"

    VISUALIZATION_TASK = 'Visualization_Task'
    class StructuralTask:
        """
        Enum-like class containing classes defining structural (i.e. objective)
        low-level tasks.
        """
        STRUCTURAL_TASK = "Structural_Task"
        class ReadingTask:
            RETRIEVE_VAL = "Retrieve_Value_Task"  # bars -> attributes, values
            FILTER = "Filter_Task"  # attributes, values -> bars
            APPLY_QFILTER = "Apply_Query_Filter_Task"  # list<QueryFilter> -> bars
            SUMMARY = "Summary_Task"  # Compute summary
        class DerivedValueTask:
            COMPARE = 'Compare_Task'  # Compare current with others
            AVERAGE = 'Compute_Average_Task'
            SUM = 'Compute_Sum_Task'
            MEDIAN = 'Compute_Median_Task'
            MODE = 'Compute_Mode_Task'
            COUNT = 'Count_Task'
        class NavigationTask:
            GOTO_FIRST = "Go_to_First_Task"
            GOTO_LAST = "Go_to_Last_Task"
            GOTO_HIGHEST = "Go_to_Highest_Task"
            GOTO_LOWEST = "Go_to_Lowest_Task"
            JUMP = 'Jump_Task'
            MOVE_LEFT = "Move_Left_Task"
            MOVE_RIGHT = "Move_Right_Task"
            MOVE_UP = "Move_Up_Task"
            MOVE_DOWN = "Move_Down_Task"
            RESET = "Reset_Task"
            WHERE = "Where_Task"
            SET_HOME = "Set_Home_Task"
            GOTO_HOME = "Go_to_Home_Task"
        class ComparisonTask:
            COMPUTE_DERIVED_VAL = "Compute_Derived_Value_Task"
            FIND_EXTREMUM = "Find_Extremum_Task"
            FIND_MAXIMUM = 'Find_Maximum_Task'
            FIND_MINIMUM = 'Find_Minimum_Task'
            RANGE = "Determine_Range_Task"
            SORT = "Sort_Task"
        class CorrelationTask:
            CLUSTER = "Cluster_Task"
            CORRELATE = "Correlate_Task"
        class DistributionTask:
            FIND_ANOMALIES = "Find_Anomalies_Task"
            CHARACTERIZE_DISTRIBUTION = "Characterize_Distribution_Task"

    class CombinationTask:
        COMPOSITION = "Composition_Task"
        SUPERIMPOSITION = "Superimposition_Task"

    class TaskProperty:
        """
        Object and datatype properties related to tasks
        """
        HAS_LOW_LEVEL_TASK = "has_low_level_task"
        HAS_DESCRIPTION = "task_has_high_level_description"
        HAS_QUERY = "task_has_query"
        HAS_RESULT_NUMERICAL = "task_has_numerical_result"
        HAS_RESULT_SPOKEN = "task_has_spoken_result"
        HAS_ORDER = "hasOrder"
        IS_INTENTION = "task_is_intention"
        HAS_VERBALIZATION = "task_has_verbalization"

    SYNT_ENTS = []  # Syntactic Entities Array i.e. ['GRAPHIC_OBJECT', ... ]
    SYNT_ROLES = []  # Syntactic Roles Array i.e. ['AXIS', 'CONTAINER', ... ]

    def count(self, element):
        """
        Returns the number of instances of the given element or the number of elements with the given syntactic role
        """
        cnt = 0
        if element:
            normElement = self.normalizeItem(element)
            category = self.itemEntityCategory(normElement)
            if category == self.SyntacticEntity.SYNTACTIC_ROLE:
                cnt = len(set(self.getElementsWithRole(normElement + "_SR")))
            else:
                cnt = len(set(self.getInstances(normElement)))
        return cnt

    def getChartTitle(self):
        """
        Returns the title of the whole chart
        @return sting: The title (or titles concatenated with commas), None
        if not found
        """
        chart = self.getInstances(self.PrimaryGraphicRepresentation.STATISTICAL_CHART)
        if chart:
            # A chart is labeled by its title
            lbls = set(self.getLabelsOfElement(chart[0]))
            titles = ", ".join([self.getText(l) for l in lbls if l])
            if titles:
                return titles
        return None

    def getConstituentElements(self, element):
        """
        Returns the elementary objects that make up the given element
        :param element: an element's name
        :return a list of elementary object instance names
        """
        subelements = set()
        if element:
            svgElements = self.getSVGElements(element)
            for svg in svgElements:
                tmpElements = self.getElementsWithSVGElement(svg)
                for e in tmpElements:
                    if e != element:
                        types = self.getClassOfElement(e)
                        if (self.SyntacticEntity.ELEMENTARY_GO in types
                            or self.SyntacticEntity.COMPOSITE_SYMBOL in types):
                            subelements.add(e)
        return list(subelements)

    def getContainerElements(self, element):
        """
        Returns the Composite Graphic Objects containing the given Elementary
        Graphic Object
        :param element: the name of an Elementary_GO instance
        :return list<string>: the name of all Composite_GO instances that
        contain the element
        """
        containers = set(self.getInstances(self.SyntacticEntity.COMPOSITE_GO))
        svgElems = self.getSVGElements(element)
        for svgElem in svgElems:
            containers &= set(self.getElementsWithSVGElement(svgElem))
        return containers

    def getElementsWithRole(self, role, type="syntactic", ns=None):
        """
        Returns a list of elements with a given role
        """
        if not ns:
            ns = self.VIS_NS
        if type == "syntactic":
            property = self.SyntacticProperty.HAS_SYNTACTIC_ROLE
        else:
            property = self.SyntacticProperty.HAS_INFORMATIONAL_ROLE
        return self.getSubjects(property,
                               role)

    def getRolesOfElement(self, element):
        """
        Returns the roles of a given element (has_syntactic_role)
        :param element: an element's name
        :return a list with role names
        """
        return self.getObjects(element,
                               self.SyntacticProperty.HAS_SYNTACTIC_ROLE)

    def elementHasRole(self, element, role, type="syntactic", ns=None):
        """
        Returns whether the given element has the given syntactic role
        :param element: an element's name
        :param role: an role's name. "any" can be used, in which case True
        will be returned (useful as a default in filters)
        :param type: "syntactic" or "informational" role
        :return TRUE if the triple (element, property, role) exists;
                FALSE otherwise
        """
        if role == "any":
            return True
        else:
            if not ns:
                ns = self.VIS_NS
            if type == "syntactic":
                property = self.SyntacticProperty.HAS_SYNTACTIC_ROLE
            else:
                property = self.SyntacticProperty.HAS_INFORMATIONAL_ROLE
            return self.tripleExists(element, property, role, "object", ns)

    def yieldTextElement(self):
        """
        Yields a text literal in the object of a has_text datatype property occurrence
        :return: (URIRef, URIRef, Literal): subject (graphic object), property (has_text), and object (text)
        of each property occurrence
        """
        if self.graph:
            propertyURI = URIRef("%s#%s" % (self.VIS_NS, self.SytacticDataProperty.HAS_TEXT))
            for s, o in self.graph.subject_objects(propertyURI):
                yield s, propertyURI, o

    def getElementsWithText(self, text):
        """
        Returns a generator of elements with a given text (has_text
        property subjects)
        :param text: the text to find in the label
        """
        return self.getSubjects(self.SytacticDataProperty.HAS_TEXT,
                               text, propertyType="datatype")

    def getText(self, element):
        """
        Returns the text associated to a given element
        :param name: the name of the element
        :return string: the text of the element or None
        """
        text = None
        if element:
            text = self.getValue(element, self.SytacticDataProperty.HAS_TEXT)
            if text and type(text) == rdflib.term.Literal:
                text = text.toPython()
        return text

    def getChartMeasurementUnit(self, axis=None):
        """
        Returns the units the chart is concerned about
        :param axis: string; name of an axis from the chart; None to fetch default axis
        :return: string: a measurement unit
        """
        if axis is None:
            axis = self.getMetricAxis()
        return self.getMetricAxisMeasurementUnit(axis)

    def getChartMeasurementDataType(self, axis=None):
        """
        Returns the datatype of the information expressed by the given axis of the chart, if available
        :param axis: string; name of an axis from the chart; None to fetch default axis
        :return: string: a datatype name, None if not available
        """
        dtype = None
        if axis is None:
            axis = self.getMetricAxis()
        info = self.getValue(axis, self.StatisticalProperty.EXPRESSES_CARDINAL_INFORMATION)
        if info:
            axis_type = self.getValue(info, self.SyntacticProperty.HAS_DATATYPE)
            if axis_type:
                dtype = axis_type
        return dtype

    def getMetricAxis(self):
        """
        Returns the metric axis of the chart (usually the vertical one)
        @return string: the name of the metric axis element
        """
        axisList = self.getElementsWithRole(self.SyntacticRoles.AXIS)
        for axis in axisList:
            if self.elementHasRole(axis, self.InformationalRoles.SPATIAL_REFERENCE_OBJECT, "informational"):
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
            cardinalInfo = self.getObjects(axis, self.StatisticalProperty.EXPRESSES_CARDINAL_INFORMATION)
            if cardinalInfo:
                if len(cardinalInfo) == 1:
                    units = cardinalInfo[0].lower().replace("_", " ")
                    return units
                else:
                    raise Exception("Axis %s is associated with more than one cardinal information." % axis)

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

    def lengthOfElement(self, element):
        """
        Returns the length of a given element as returned by its has_length
        datatype property.
        @param element: the name of an instance in the ontology
        @return float: the length of the element, -1 if not found
        """
        length = -1.0
        if element:
            l = self.getValue(element, self.SytacticDataProperty.HAS_LENGTH)
            if l:
                length = float(l)
        return length

    def lengthOfAxis(self, axis):
        """
        Returns the length of a given labeled axis. If the axis length can not
        be retrieved, computes and saves it
        :param axis: the name of the axis
        :return int: the length in pixels of the axis as given by the position
        of its labels in the Y axis
        """
        length = 0
        if axis:
            length = self.lengthOfElement(axis)
            if length <= 0:
                length = self.computeAxisLengthFromLabels(axis)
        return length

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
            topLabel = self.getValue(axis, self.MetricAxisProperty.HAS_TOP_LABEL)
            bottomLabel = self.getValue(axis, self.MetricAxisProperty.HAS_BOTTOM_LABEL)
        return (str(topLabel), str(bottomLabel))

    def computeAxisLengthFromLabels(self, axis):
        """
        Infers the length of a metric axis from its labels.
        :param axis: the name of the axis
        :return: float; length of the axis. The ontology gets updated with the new information as well.
        """
        length = 0.0
        labels = self.labelsOfAxis(axis)
        topLabel = None
        bottomLabel = None
        topYCoor = float_info.max  # Y coordinates are inverted in SVG; the topmost Y coordinate has the lowest value
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
                                           length, datatype=XSD.float, functional=True)
            self.addObjectPropertyTriple(axis,
                                         self.MetricAxisProperty.HAS_TOP_LABEL,
                                         topLabel, functional=True)
            self.addObjectPropertyTriple(axis,
                                         self.MetricAxisProperty.HAS_BOTTOM_LABEL,
                                         bottomLabel, functional=True)
        return length


    def getIndependentVariables(self):
        """
        Returns the name of the classes representing Independent Variables in
        the ontology
        @return list<string>: names of the independent variables
        """
        return self.getSubclasses(self.StatisticalVarType.INDEPENDENT_VARIABLE)

    def getOrientation(self, element):
        """
        Returns the named orientation of the object (if any)
        :param name: the name of the element
        :return string: the named orientation e.g. Vertical_Orientation
        """
        o = None
        if element:
            o = self.getValue(element, self.SyntacticProperty.HAS_ORIENTATION)
            if o and type(o) == rdflib.term.Literal:
                o = o.toPython()
        return o

    def getLabels(self):
        """
        Returns all entities with a label synt. role
        """
        return self.getElementsWithRole(self.SyntacticRoles.LABEL)

    def getLabelsWithText(self, labelText):
        """
        Returns a list with the label instances that have the given text
        :param labelText: the text of the label
        :return list<string>: a list of instance names
        """
        elements = []
        if labelText:
            labelElements = self.getElementsWithText(labelText)
            for labelElement in labelElements:
                if self.elementHasRole(labelElement, self.SyntacticRoles.LABEL):
                    elements.append(labelElement)
        return elements

    def getElementsLabeledByText(self, labelText):
        """
        Returns a list with all elements labeled by the labels containing the
        text passed as a parameter
        :param labelText: the text of the label; NOT the label element's name
        :return list<string>: a list of instance names
        """
        elements = []
        if labelText:
            labelElements = self.getElementsWithText(labelText)
            for labelElement in labelElements:
                if self.elementHasRole(labelElement, self.SyntacticRoles.LABEL):
                    elements.extend(self.getSubjects(
                                           self.SyntacticProperty.IS_LABELED_BY,
                                           labelElement))
        return elements

    def getLabelsOfElement(self, element):
        """
        Returns a list of all the labels assigned to the given element
        :param element: the name of an instance
        :return list<string>: a list of label instance names
        """
        labels = []
        if element:
            labels = self.getObjects(element,
                                     self.SyntacticProperty.IS_LABELED_BY)
        return labels

    def getSVGElements(self, element):
        """
        Returns the constituent SVG elements of an instance
        :param element (string): an instance name
        :return list<string>: a list of SVGElement IDs
        """
        elements = []
        if element:
            elements = self.getObjects(element,
                                       self.SytacticDataProperty.HAS_SVG_ELM)
        return elements

    def getElementsWithSVGElement(self, SVGElement):
        """
        Returns the instances associated with the given SVG element
        :param SVGElement (string): the ID of a SVG element (path, text...)
        :return list<string>: a list of entity individual names
        """
        elements = []
        if SVGElement:
            elements = self.getSubjects(self.SytacticDataProperty.HAS_SVG_ELM,
                                        SVGElement, propertyType="datatype")
        return elements

    def getElementsContainedInSVGElements(self, SVGElements):
        """
        Returns the instances that satisfy the condition that all their
        constituent SVG elements are within the given ones
        :param SVGElements list<string>: SVG IDs
        :return list<string>: a list of entity individual names
        """
        elements = []
        if SVGElements:
            SVGElmsSet = set(SVGElements)
            candidates = set()
            for svge in SVGElmsSet:
                candidates |= set(self.getElementsWithSVGElement(svge))
            if candidates:
                for c in candidates:
                    candidateSVGElems = set(self.getSVGElements(c))
                    if candidateSVGElems <= SVGElmsSet:
                        elements.append(c)
        return elements

    def elementsInRelation(self, relation, roles="any", type="syntactic"):
        """
        Returns GOs (with a given role) instance names belonging to instances
        of the given graphic relation
        :param relation: name of the Graphic Relation class
        :param roles: a list of syntactic roles to filter the output objects
        (optional), "any" for all.
        :param type: the type of role: syntactic (default) or informational
        :return dict<string, list<string>> Keys are relation instance names,
        values are lists of GO instances belonging to the relation
        """
        elements = defaultdict(list)
        relations = self.getInstances(relation)
        if relations:
            for r in relations:
                relSVGElms = self.getSVGElements(r)
                if relSVGElms:
                    for e in self.getElementsContainedInSVGElements(relSVGElms):
                        add = False
                        if roles != "any":
                            for role in roles:
                                if not add and self.elementHasRole(e, role, type):
                                    add = True
                        else:
                            add = True
                        if add:
                            elements[r].append(e)
        return elements

    def getNavigationProperties(self, node):
        """
        Returns the navigation properties of a given node and their current
        values.
        :param node: the instance name of a graphic object
        :return dict<string, mixed>: key is the property name, value is the
        object of the (node, p, value) triple of the ontology converted to
        its Python type. Data is actually fetched from the user session, not the ontology.
        """
        props = {}
        if node:
            for p in self.NAV_PROP:
                prop = getattr(self.NavigationDataProperty, p)
                navVal = self.getValue(node, prop)
                if navVal:
                    props[prop] = navVal
            #  Fetch non-persisted properties from user session
            if self.isCurrent(node):
                props[self.NavigationDataProperty.IS_CURRENT] = True
            if self.isHomeNode(node):
                props[self.NavigationDataProperty.IS_HOME_NODE] = True
            user_tags = self.getUserLabels(node)
            if user_tags:
                props[self.NavigationDataProperty.HAS_USER_LABEL] = user_tags
        return props

    def navigate(self, actions):
        """
        Default navigation method. Needs to be overridden by a specialized ontology handler.
        :param actions: a list of actions to be taken
        :return: list<string> a list of objects that have the navigation focus
        """
        return []

    def getPreviousNodes(self):
        """
        Return the instance name of the previously visited graphic elements
        :return list<string>: instance name of previous graphic objects in the current session
        """
        prev_sess_var = c.SESS_PREV_NODES % self.sess_id
        return session.get(prev_sess_var, [])

    def isPrevious(self, node):
        """
        Returns whether the given element belong to any of the previously
        visited graphic elements
        :param node: instance name of a graphic object
        :return boolean: whether 'node' was previously selected by the user
        while navigating the graphic.
        """
        isprev = False
        if node:
            isprev = node in self.getPreviousNodes()
        return isprev

    def getCurrentNodes(self):
        """
        Return the instance name of the currently selected graphic elements
        :return list<string>: instance name of current graphic objects in current session.
        """
        sess_var = c.SESS_CURR_NODES % self.sess_id
        return session.get(sess_var, [])

    def isCurrent(self, node):
        """
        Returns whether the given element belong to any of the currently being
        visited graphic elements
        :param node: instance name of a graphic object
        :return boolean: whether 'node' is currently selected by the user
        while navigating the graphic.
        """
        iscur = False
        if node:
            iscur = node in self.getCurrentNodes()
        return iscur

    def setCurrentNodes(self, elms):
        """
        Set the given elements as the current ones, and set the previous current
        elements as the previous visited ones
        :param elms iterable: the new current element instance names
        """
        curr_sess_var = c.SESS_CURR_NODES % self.sess_id
        prev_nodes = session.get(curr_sess_var, [])
        if prev_nodes:
            prev_sess_var = c.SESS_PREV_NODES % self.sess_id
            session[prev_sess_var] = prev_nodes
        session[curr_sess_var] = elms

    def getHomeNodes(self):
        """
        Return the instance name of the currently chosen graphic elements as
        home nodes
        :return list<string>: instance names of home nodes in the current session.
        """
        home_sess_var = c.SESS_HOME_NODES % self.sess_id
        return session.get(home_sess_var, [])

    def isHomeNode(self, node):
        """
        Returns whether the given element belong to any of the home nodes set
        by the user
        :param node: instance name of a graphic object
        :return boolean: whether 'node' is any of the home nodes set by the user
        """
        ishome = False
        if node:
            ishome = node in self.getHomeNodes()
        return ishome

    def setHomeNodes(self, elms):
        """
        Set the given elements as the current home nodes
        :param elms iterable: the new home node element instance names
        """
        home_sess_var = c.SESS_HOME_NODES % self.sess_id
        session[home_sess_var] = elms

    def getNavigationNodes(self, p):
        """
        Return the instance name of the graphic elements with the given
        navigation property set to True
        :param p: the name of a datatype property with boolean range
        :return list<string>: instance names of graphic elements with the given
        property set to True
        """
        return self.getSubjects(p, True, 'datatype', XSD.boolean)

    def setNavigationNodes(self, p, nodes):
        """
        Set the given elements as having the given datatype boolean property (any
        of the properties used for navigation tasks), and deletes all previous
        assertions of the property.
        :param p: the name of a datatype property with boolean range
        :param nodes iterable: element instance names to be used as property
        subjects
        """
        if len(nodes) > 0:
            newFound = False
            for new in nodes:
                if new:
                    newFound = True
                    self.addDataTypePropertyTriple(new, p, True, XSD.boolean)
            if newFound:
                oldCurrent = self.getNavigationNodes(p)
                for old in oldCurrent:
                    if old not in nodes:
                        self.removeDataTypePropertyTriple(old, p)

    def getUserLabels(self, element):
        """
        Returns the user-defined tags for the given element
        :param element: an instance name
        :return string: the user-defined information for the element, an empty string if not found
        """
        ul = ""
        if element:
            sess_var = c.SESS_USER_LABELS % self.sess_id
            labels = session.get(sess_var, {})
            ul = labels.get(element, "")
        return ul

    def getElementsWithUserLabels(self, userTags, negate=False):
        """
        Return the elements of the ontology tagged by the user with all the given user tags
        :param userTags: list<string> user tags to search for
        :param negate: boolean; whether to logically negate the results (default False)
        :return: list<string>: elements that have been labeled by the current user with all the given tags
        """
        user_set = set([quick_norm(t) for t in userTags])
        elements = set()
        if userTags:
            sess_var = c.SESS_USER_LABELS % self.sess_id
            labels = session.get(sess_var, {})
            for element, e_tags in labels.iteritems():
                tag_set = set([quick_norm(l) for l in e_tags.replace(';', ',').split(",")])
                if tag_set.issubset(user_set) or (negate and not any(tag in tag_set for tag in user_set)):
                    elements.add(element)
        return list(elements)

    def setUserLabels(self, elements, userTags):
        """
        Adds the given string to the given elements as user-defined labels
        :param iterable<string> or string: a list of graphic object instance names or a single element name
        :param string: userTags: the user data to add to the elements. The string will be copied to all elements.
        """
        if elements and userTags:
            sess_var = c.SESS_USER_LABELS % self.sess_id
            labels = session.get(sess_var, {})
            if not isinstance(elements, list):
                elements = [elements]
            for e in elements:
                labels[e] = userTags
            session[sess_var] = labels

    def isLowLevelTask(self, task):
        """
        Returns whether the given task is a low-level task
        :param task: a task instance name
        :return boolean: True if the task is a low-level task, False otherwise
        """
        return self.StructuralTask.STRUCTURAL_TASK in self.getClassOfElement(task)

    def getTaskOfVerbalization(self, verb, stripns=True):
        """
        Given a potential task verbalization, return its class
        :param verb: string; verbalization of a task
        :param stripns: boolean; whether to remove the namespace from the results
        :return: string: Task name; None if no task found
        """
        task = None
        verb_p = "%s#%s" % (self.VIS_NS, self.TaskProperty.HAS_VERBALIZATION)
        triples = self.contextOfLiteral(verb.lower(), dtype=XSD.string)
        for s, p, o in triples:
            if p == verb_p:
                task = self.stripNamespace(s) if stripns else s
                break
        return task

    def getTaskVerbalizations(self, tasks='all', ns=None):
        """
        Return a list of task verbalizations (keywords that may appear in the user query when referring to the task)
        :param task: list<string>: Task instance names, 'all' to consider all instances
        :return: dict<string; list<string>: {task: list of verbalizations for task}
        """
        verbs = {}
        if not isinstance(tasks, list):
            if tasks == 'all':
                task = '%s#%s' % (self.VIS_NS, self.VISUALIZATION_TASK)
                tasks = self.getSubclasses(task, self.VIS_NS)
            elif isinstance(tasks, basestring):
                tasks = [tasks]
            else:
                return verbs
        task_instances = []
        subclasses = []
        for t in tasks:
            subclasses.extend(self.getSubclasses(t, ns))
            task_instances.extend(self.getInstances(t))
        for sc in subclasses:
            task_instances.extend(self.getInstances(sc))
        for t in task_instances:
            if t in verbs:
                verbs[t].extend(self.getObjects(t, self.TaskProperty.HAS_VERBALIZATION))
            else:
                t_v = self.getObjects(t, self.TaskProperty.HAS_VERBALIZATION)
                if t_v:
                    verbs[t] = t_v
        return verbs

    def getTaskQuery(self, task):
        """
        Return the natural language description of a task
        :param task: a task instance name
        :return string: NL description of the task according to its HAS_QUERY
        property
        """
        q = None
        if task:
            p = self.TaskProperty.HAS_QUERY
            q = self.getValue(task, p)
        return q

    def getTaskSpokenResult(self, task):
        """
        Return the natural language result of a task
        :param task: a task instance name
        :return string: NL description of the task's result according to its
        HAS_RESULT_SPOKEN property
        """
        q = None
        if task:
            p = self.TaskProperty.HAS_RESULT_SPOKEN
            q = self.getValue(task, p)
        return q

    def getTaskSummary(self, task):
        """
        Return the natural language summary of a high-level task
        :param task: a task instance name
        :return string: NL summary of the task according to its HAS_DESCRIPTION
        property
        """
        q = None
        if task:
            p = self.TaskProperty.HAS_DESCRIPTION
            q = self.getValue(task, p)
        return q

    def getLowLevelTasks(self, subtype='all'):
        """
        Return all low-level task instances of the given subtypes
        :param subtype: a class name to return only taks belonging to that
        class; 'all' for all low-level tasks
        :return list<string>: instance names of tasks in the ontology
        """
        tasks = []
        if subtype:
            if subtype == 'all':
                taskClass = self.StructuralTask.STRUCTURAL_TASK
            else:
                taskClass = subtype
            tasks =  self.getInstances(taskClass)
        return tasks

    def getSubTasks(self, task):
        """
        Return the low-level tasks that make up a given high-level task
        :param task: a composition or superimposition task instance name
        :return dict<int, string>: keys are task order values; values are task
        instance names
        """
        subtasks = {}
        if task:
            p = self.TaskProperty.HAS_LOW_LEVEL_TASK
            subt = self.getObjects(task, p)
            for t in subt:
                taskOrder = self.getValue(t, self.TaskProperty.HAS_ORDER)
                if taskOrder:
                    subtasks[int(taskOrder)] = t
        return subtasks

    def getIntentionTasks(self):
        """
        Return the task instances marked as the author's intention
        :return list<string>: a list of task instance names
        """
        p = self.TaskProperty.IS_INTENTION
        return self.getSubjects(p, True, 'datatype', XSD.boolean)

    def taskNeedsSummary(self, task):
        """
        Returns whether a summary of the task should be output after computing it
        :param task: A SemanticConcept instance of an analytical task
        :return: True if summary ought to be added after task answer, false otherwise
        """
        summary = False
        if task:
            req_sum = [self.StructuralTask.DerivedValueTask.AVERAGE,
                       self.StructuralTask.DerivedValueTask.MEDIAN,
                       self.StructuralTask.DerivedValueTask.MODE,
                       self.StructuralTask.DerivedValueTask.COUNT,
                       self.StructuralTask.DerivedValueTask.SUM,
                       self.StructuralTask.DistributionTask.CHARACTERIZE_DISTRIBUTION]
            task_name = self.stripNamespace(task.task)
            if task_name in req_sum:
                summary = True
        return summary

    def getCoordinate(self, element, coor="x"):
        """
        Returns the chosen coordinate of a given element
        :param element: the name of an instance in the ontology
        :param coor: the coordinate; "x" (default) or "y"
        :return float: the coordinate, False if not found
        """
        coorRet = False
        if element:
            if coor=="x":
                prop = self.SytacticDataProperty.HAS_X_COOR
            else:
                prop = self.SytacticDataProperty.HAS_Y_COOR
            l = list(self.getObjects(element, prop))
            if len(l) > 0:
                if len(l) > 1:
                    raise Exception("Element %s has more than one x coordinate."
                                    % element)
                else:
                    coorRet = float(l[0])
        return coorRet

    def itemEntityCategory(self, normalizedItem):
        """
        Tries to infer the kind of entity its argument belongs to
        :param normalizedItem: A normalized single word
        :return: a category (Main, Role, None...)
        """
        category = self.SyntacticEntity.NONE
        if normalizedItem:
            checkItem = normalizedItem.upper()
            if checkItem in self.SYNT_ENTS or (checkItem + "_GO") in self.SYNT_ENTS:
                category = "Main"
            elif checkItem in self.SYNT_ROLES:
                category = self.SyntacticEntity.SYNTACTIC_ROLE
        return category

    def slopeBetweenPoints(self, p1, p2):
        """
        Returns the slope of the line segment defined by the given points in the 2D plane
        :param p1: (float, float); x, y coordinates of the first point
        :param p2: (float, float); x, y coordinates of the second point
        :return: float: slope between points, in degrees
        """
        import math
        numerator = float(p1[1]) - p2[1]
        denominator = float(p1[0]) - p2[0]
        if abs(denominator) >= 1.0:
            return -math.degrees(math.atan(numerator/denominator))
        else:  # X coordinates less than 1px apart, consider them aligned
            return 90.0 if numerator < 0 else -90.0

    def lineIsMonotonic(self, slope_list, tol=5.0):
        """
        Returns whether a line, given by the slopes of its segments, is monotonic with the given tolerance
        :param slope_list: list<float>: slopes (in degrees) of the segments between line's constituent points
        :param tol: float; degree from which a slope is not considered to be flat. Default 5.
        :return: True if the line is monotonically increasing or decreasing; False otherwise
        """
        monotonic = True
        if len(slope_list) > 1:
            for i, d in enumerate(slope_list[1:], 1):
                prev = slope_list[i - 1]
                if d * prev < 0 and (abs(d) > tol or abs(prev) > tol):
                    monotonic = False
                    break
        return monotonic

    def straightSlopeLabel(self, points):
        """
        Given a number of data points, returns a label for the slope of the line segments between them
        :param points: list<(float, float)>: x and y coordinates of points in the 2D place
        :return: slope expressed in natural language e.g. 'increasing', 'decreasing', 'accelerating', etc.
        """
        label = ''
        n_points = len(points)
        if n_points == 2:
            deg = self.slopeBetweenPoints(*points)
            increase = points[0][1] >= points[1][1]
            slope = abs(deg)
            if slope < 2:
                label = 'flat'
            elif slope < 5:
                label = 'almost flat'
            elif slope < 15:
                label = 'slow'
            elif slope < 30:
                label = 'moderate'
            elif slope < 45:
                label = 'sharp'
            elif slope < 75:
                label = 'very steep'
            else:
                label = 'extremely steep'
            if slope > 5:
                label += ' increase' if increase else ' decrease'
            else:
                label += ' course'
        elif n_points == 3 or n_points == 4:
            degs = [self.slopeBetweenPoints(a, b) for a, b in zip(points, points[1:])]
            if self.lineIsMonotonic(degs):
                if all(d >= 15 for d in degs):
                    label = 'accelerating '
                elif all(d <= -15 for d in degs):
                    label = 'decelerating '
                label += self.straightSlopeLabel([points[0], points[-1]])
            else:
                first_slope = self.straightSlopeLabel([points[0], points[1]])
                second_slope = self.straightSlopeLabel([points[1], points[2]])
                label = "%s followed by a %s" % (first_slope, second_slope)
                if n_points == 4:
                    label += " followed by a %s" % (self.straightSlopeLabel([points[2], points[3]]))
        elif n_points > 4:
            degs = []
            i = 0
            while i < n_points - 1:
                found = False
                j = i + 1
                while not found and j < n_points:
                    deg = self.slopeBetweenPoints(points[i], points[j])
                    if abs(deg) < 90.0:  # Vertical changes indicate bars are superimposed; ignore them
                        degs.append(deg)
                        found = True
                    else:
                        j += 1
                i = j
            trend_changes = self.significantTrendChange(degs, max_n=10, tol=30.0)
            start = 0
            for i in trend_changes:
                if start > 0:
                    label += ' followed by a '
                label += self.straightSlopeLabel([points[start], points[i]])
                start = i
            if trend_changes:
                label += ' followed by a '
            label += self.straightSlopeLabel([points[start], points[-1]])
        return label

    def significantTrendChange(self, degrees, max_n=10, tol=5.0):
        """
        Given a line divided into segments, choose which changes in the line's trend are significant enough to be
        displayed to the user
        :param degrees: list<float>: slopes (in degrees) of the segments between line's constituent points
        :param max_n: int; maximum number of trend changes to display, as % of the total line segments
        :param tol: float; tolerance in degrees below which the line is considered flat
        :return: list<int> indexes of the significant trend changes
        """
        trend_changes = []
        diffs = [0.0]
        n_slopes = len(degrees)
        if n_slopes > 1:
            n = max(1, max_n * n_slopes / 100)
            for i, di in enumerate(degrees):
                j = i + 1
                if j < n_slopes:
                    dj = degrees[j]
                    if self.lineIsMonotonic([di, dj], tol):
                        diffs.append(0.0)
                    else:
                        diffs.append(abs(di - dj))
            threshold = sorted(diffs)[-n]
            c = 0
            for k, d in enumerate(diffs):
                if d >= threshold and d >= tol:
                    trend_changes.append(k)
                    c += 1
                    if c == n:
                        break
        return trend_changes

    def normalizeItem(self, item, type='entity'):
        """
        Normalizes the name of a given Entity or Property.
        Entities are capitalized, properties are not.
        """
        normItem = item
        if item:
            s = item.replace(' ', '_')
            if type == 'entity':
                normItem = '_'.join(word[0].upper() + word[1:].lower()
                                for word in s.split('_'))
                """Deal with class ids e.g. GO in Elementary_GO """
                if len(normItem) > 3 and normItem[-3] == "_":
                    classid = normItem[-2:].upper()
                    if classid in self.ENTITY_ABBRV:
                        normItem = "%s%s" % (normItem[:-2], classid)
                elif normItem.lower() in c.NavFilters:  # Navigation Filters
                    normItem = c.NavFilters[normItem.lower()]
                # else:
                #    normItem = normItem.replace('_', ' ')
            else:
                normItem = s
        else:
            normItem = ""
        return normItem
