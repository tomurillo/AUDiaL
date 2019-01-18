import rdflib
from rdflib.term import URIRef
from rdflib import RDF, RDFS, OWL, Namespace, Literal, XSD
from util import *
import os
import bsddb
import const as c
import constants as o_c
from collections import defaultdict

class UpperOntology(object):
    """ Main Vis. Ontology class containing common attributes and methods"""

    class SyntacticEntity:
        """Enum-like class containing upper visualization ontology classes"""
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
        """Object-to-Object graphic relations"""
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
        """Upper visualization ontology object properties"""
        HAS_SYNTACTIC_ROLE = "has_syntactic_role"
        IS_SYNTACTIC_ROLE_OF = "is_syntactic_role_of"
        HAS_INFORMATIONAL_ROLE = "has_informational_role"
        IS_LABELED_BY = "is_labeled_by"
        IS_LABEL_FOR = "is_label_for"
        HAS_COLOR = "has_color_named"
        HAS_ORIENTATION = "has_orientation_named"

    class StatisticalProperty:
        """Object properties related to statistical elements"""
        EXPRESSES_INFORMATION = "expresses_information"
        EXPRESSES_CARDINAL_INFORMATION = "expresses_cardinal_information"
        EXPRESSES_NOMINAL_INFORMATION = "expresses_nominal_information"
        EXPRESSES_ORDINAL_INFORMATION = "expresses_ordinal_information"

    class NavigationObjectProperty:
        """Object Properties that aid with navigation"""
        HAS_PREVIOUS = "has_previous_node"
        HAS_NEXT = "has_next_node"

    class NavigationDataProperty:
        """Datatype Properties that aid with navigation"""
        HAS_ORDER = "hasOrder"
        IS_CURRENT = "isCurrentNode"
        IS_HOME_NODE = "isHomeNode"
        IS_PREVIOUS_VISITED = "isPreviousVisitedNode"
        HAS_USER_LABEL = "has_user_label" # User-defined element label
        HAS_SPECIFICITY = "has_specificity"
        HAS_DISTANCE_SCORE = "has_distance_score"
        HAS_PROP_FINAL_SCORE = "has_property_final_score"

    class SytacticDataProperty:
        """Upper visualization ontology datatype properties"""
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

    class StructuralTask:
        """
        Enum-like class containing classes defining structural (i.e. objective)
        low-level tasks.
        """
        STRUCTURAL_TASK = "Structural_Task"
        class ReadingTask:
            RETRIEVE_VAL = "Retrieve_Value_Task" # bars -> attributes, values
            FILTER = "Filter_Task" # attributes, values -> bars
        class NavigationTask:
            GOTO_FIRST = "Go_to_First_Task"
            GOTO_LAST = "Go_to_Last_Task"
            GOTO_HIGHEST = "Go_to_Highest_Task"
            GOTO_LOWEST = "Go_to_Lowest_Task"
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

    """Syntactic Entities Array i.e. ['GRAPHIC_OBJECT', ... ]"""
    SYNT_ENTS = []

    """Syntactic Roles Array i.e. ['AXIS', 'CONTAINER', ... ]"""
    SYNT_ROLES = []

    def __init__(self, RDFpath):
        self.VIS_NS = c.VIS_NS
        self.graph = rdflib.ConjunctiveGraph("Sleepycat")

        if not os.path.isdir(c.STOREDIR):
            os.makedirs(c.STOREDIR)
        self.open(c.STOREDIR)
        if not self.graph and RDFpath is not None:
            self.load(RDFpath)
        """Abbreviations of entities e.g. used as suffixes in entity names"""
        self.ENTITY_ABBRV = {"GO" : self.SyntacticEntity.GRAPHIC_OBJECT,
                             "GR" : self.SyntacticEntity.GRAPHIC_RELATION,
                             "GS" : self.SyntacticEntity.GRAPHIC_SPACE,
                             "IR" : self.SyntacticEntity.INFORMATIONAL_ROLE,
                             "SR" : self.SyntacticEntity.SYNTACTIC_ROLE,
                             "VA" : self.SyntacticEntity.VISUAL_ATTRIBUTE
                             }
        self.SYNT_ENTS = [attr for attr in dir(self.SyntacticEntity())
                        if not callable(attr) and not attr.startswith("__")]
        self.SYNT_ROLES = [attr for attr in dir(self.SyntacticRoles())
                        if not callable(attr) and not attr.startswith("__")]
        self.NAV_PROP = [attr for attr in dir(self.NavigationDataProperty())
                        if not callable(attr) and not attr.startswith("__")]

    def open(self, path):
        """
        Open or create a persistent ontology graph
        """
        try:
            self.graph.open(path, create=False)
        except bsddb.db.DBNoSuchFileError:
            self.graph.open(path, create=True)

    def load(self, fileName):
        """
        Load a rdf file into the graph object
        """
        if fileName:
            self.path = fileName
            self.graph.load(fileName)

    def close(self):
        """
        Close graph to avoid lock entries leak
        """
        if self.graph:
            self.graph.close()
            self.graph = None

    def count(self, element):
        """
        Returns the number of elements
        """
        c = 0
        if element:
            normElement = self.normalizeItem(element)
            category = self.itemEntityCategory(normElement)
            if category == self.SyntacticEntity.SYNTACTIC_ROLE:
                c = len(set(self.getElementsWithRole(normElement + "_SR")))
            else:
                c = len(set(self.getInstances(normElement)))
        return c

    def getClasses(self, ns='all'):
        """
        Returns all classes in the ontology
        :param ns: namespaces to consider (string or list), 'all' for all
        :return: list<string>: a list of class URIs
        """
        if not ns:
            ns = self.VIS_NS
        classes = [i for i in self.graph.subjects(RDF.type, URIRef("%s#%s" % (c.OWL_NS, "Class")))]
        if ns == 'all':
            return classes
        else:
            if not isinstance(ns, list):
                ns = [ns]
            return [i for i in classes if self.getNamespace(i) in ns]

    def getProperties(self, prop_type='all', ns='all'):
        """
        Returns properties in the ontology
        :param prop_type: 'object', 'datatype', or 'all'. The kind of properties to consider.
        :param ns: namespaces to consider (string or list), 'all' for all
        :return: list<string>: a list of class URIs
        """
        if not ns:
            ns = self.VIS_NS
        props = []
        if prop_type in ['all', 'object']:
            props = [i for i in self.graph.subjects(RDF.type,
                                                      URIRef("%s#%s" % (c.OWL_NS, "ObjectProperty")))]
        dtype_prop = []
        if prop_type in ['all', 'datatype']:
            dtype_prop = [i for i in self.graph.subjects(RDF.type,
                                                      URIRef("%s#%s" % (c.OWL_NS, "DatatypeProperty")))]
        props.extend(dtype_prop)
        if ns == 'all':
            return props
        else:
            if not isinstance(ns, list):
                ns = [ns]
            return [i for i in props if self.getNamespace(i) in ns]

    def getInstances(self, entityName='all', stripns=True, ns=None):
        """
        Returns a list of instances of the given class
        :param entityName: name of a class in the ontology, 'all' to get all individuals regardless of class
        :param stripns: True to strip the namespace from the output (default), False otherwise
        :param ns: namespaces to consider (string or list), 'all' for all
        :return list<string>: a list of instance names or URIs, depending on the stripns parameter
        """
        if not ns:
            ns = self.VIS_NS
        instances = []
        if self.graph and entityName:
            namedIndividualURI = URIRef("%s#%s" % (c.OWL_NS, "NamedIndividual"))
            if entityName != 'all':
                entityURI = URIRef("%s#%s" % (ns, entityName))
                for instance in self.graph.subjects(RDF.type, entityURI):
                    if (instance, RDF.type, namedIndividualURI) in self.graph:
                        instances.append(instance)
            else:
                inst = [i for i in self.graph.subjects(RDF.type, namedIndividualURI)]
                if ns != 'all':
                    if not isinstance(ns, list):
                        ns = [ns]
                    instances = [i for i in inst if self.getNamespace(i) in ns]
                else:
                    instances = inst
        if stripns:
            return [self.stripNamespace(i) for i in instances]
        else:
            return instances

    def getLiterals(self):
        """
        Returns all literals in the ontology
        :return: list<string>: a list of literal values
        """
        query = """SELECT DISTINCT ?o
                   WHERE { ?s ?p ?o
                        FILTER isLiteral(?o)
                   }"""
        query_res = self.graph.query(query)
        return [row[0].toPython() for row in query_res]

    def getSubjects(self, property, obj, propertyType='object', dtype=None,
                    ns=None):
        """
        Returns a list with all subjects for a given property, object pair
        """
        if not ns:
            ns = self.VIS_NS
        subjects = []
        if self.graph and property and obj:
            propertyURI = URIRef("%s#%s" % (ns, property))
            if propertyType == 'datatype':
                if not dtype:
                    objectURI = Literal(obj)
                else:
                    objectURI = Literal(obj, datatype=dtype)
            else:
                objectURI = URIRef("%s#%s" % (ns, obj))
            subjects = self.graph.subjects(propertyURI, objectURI)
        return [self.stripNamespace(s) for s in subjects]

    def getObjects(self, subj, property, ns=None):
        """
        Returns a list with all objects for a given subject, property pair
        """
        if not ns:
            ns = self.VIS_NS
        objects = []
        if self.graph and property and subj:
            propertyURI = URIRef("%s#%s" % (ns, property))
            subjectURI = URIRef("%s#%s" % (ns, subj))
            objects = self.graph.objects(subjectURI, propertyURI)
        return [self.stripNamespace(o) for o in objects]

    def getValue(self, s, p, default=None, ns=None):
        """
        Returns the value of a functional property. An exception is raised
        if more than one (s, p, _) triples are found
        :param s: name of the subject
        :param p: name of the (functional) property
        :param default: default value to use if nothing found
        :param ns: namespace, None for default visualization NS
        """
        if not ns:
            ns = self.VIS_NS
        val = None
        if s and p:
            subjectURI = URIRef("%s#%s" % (ns, s))
            propertyURI = URIRef("%s#%s" % (ns, p))
            val = self.graph.value(subjectURI, propertyURI, default=default)
        return self.stripNamespace(val)

    def getClassOfElement(self, element, stripns=True, ns=None):
        """
        Return the Entities an individual belongs to; an empty list if none found
        :param element: and instace name
        :param stripns: boolean; whether to remove the namespace from the results
        :param ns: namespace, None for default visualization NS
        :return: a list with the names of the classes the element belongs to
        """
        classes = []
        if not ns:
            ns = self.VIS_NS
        if element:
            subjectURI = URIRef("%s#%s" % (ns, element))
            propertyURI = URIRef("%s#type" % c.RDF_NS)
            objects = self.graph.objects(subjectURI, propertyURI)
            namedIndividualURI = URIRef("%s#%s" % (c.OWL_NS, "NamedIndividual"))
            if stripns:
                classes = [self.stripNamespace(o) for o in objects if o != namedIndividualURI]
            else:
                classes = [o for o in objects if o != namedIndividualURI]
        return classes

    def getTopClasses(self, childClass, ns=None, depth=-1):
        """
        Returns the most generic parent class of the given child class
        :param childClass: The name of the child class
        :param ns: namespace, None for default visualization NS
        :param int: current depth level of search
        :return: list<string>: the URIs of the topmost parent classes (usually just one) of the given class
        """
        parents = self.getParentClasses(childClass, ns, stripns=False)
        max_parent_depth = -1
        topclasses = [childClass]
        depth += 1
        for c in parents:
            next_classes, next_depth = self.getTopClasses(c, ns, depth)
            if next_depth > max_parent_depth:
                max_parent_depth = next_depth
                topclasses = next_classes
                depth = max_parent_depth + 1
            elif next_depth == max_parent_depth:
                topclasses.extend(next_classes)
        return topclasses, depth

    def getSubclasses(self, parentClass, ns=None):
        """
        Returns all subclasses for the parent class.
        :param parentClass: The name of the parent class
        :param ns: namespace, None for default visualization NS
        :return: List<string> its subclasses
        """
        if not ns:
            ns = self.VIS_NS
        namedIndividualURI = URIRef("%s#%s" % (c.OWL_NS, "NamedIndividual"))
        propertyURI = URIRef("%s#subClassOf" % c.RDFS_NS)
        objectURI = URIRef("%s#%s" % (ns, parentClass))
        subjects = self.graph.subjects(propertyURI, objectURI)
        classes = [self.stripNamespace(s) for s in subjects
                   if s != namedIndividualURI]
        return classes

    def getParentClasses(self, childClass, ns=None, stripns=True):
        """
        Returns all parent classes for the given class.
        :param childClass: The name or URI of the child class
        :param ns: namespace, None for default visualization NS
        :param stripns: True to strip the namespace from the output (default), False otherwise
        :return: List<string> its parent classes
        """
        if not ns:
            ns = self.VIS_NS
        namedIndividualURI = URIRef("%s#%s" % (c.OWL_NS, "NamedIndividual"))
        propertyURI = URIRef("%s#subClassOf" % c.RDFS_NS)
        subjectURI = URIRef("%s#%s" % (ns, self.stripNamespace(childClass)))
        objects = self.graph.objects(subjectURI, propertyURI)
        if stripns:
            classes = [self.stripNamespace(o) for o in objects
                       if o != namedIndividualURI]
        else:
            classes = [o for o in objects if o != namedIndividualURI]
        return classes

    def getParentProperties(self, childProp, ns=None):
        """
        Returns all parent properties for the given property.
        :param childProp: The name or URI of the child property
        :param ns: namespace, None for default visualization NS
        :return: List<string> its parent classes
        """
        if not ns:
            ns = self.VIS_NS
        propertyURI = URIRef("%s#subPropertyOf" % c.RDFS_NS)
        subjectURI = URIRef("%s#%s" % (ns, self.stripNamespace(childProp)))
        objects = self.graph.objects(subjectURI, propertyURI)
        props = [self.stripNamespace(o) for o in objects]
        return props

    def instanceIsOfClass(self, instance, entity, ns=None):
        """
        Returns whether the given individual is of the given class
        :param instance: The name of the individual
        :param entity: The name of a class
        :param ns: namespace, None for default visualization NS
        :return: True if 'instance' is of type 'class'
        """
        if not ns:
            ns = self.VIS_NS
        namedIndividualURI = URIRef("%s#%s" % (c.OWL_NS, "NamedIndividual"))
        subjectURI = URIRef("%s#%s" % (ns, instance))
        propertyURI = URIRef("%s#type" % c.RDF_NS)
        objectURI = URIRef("%s#%s" % (ns, entity))
        return (subjectURI, propertyURI, namedIndividualURI) in self.graph and \
               (subjectURI, propertyURI, objectURI) in self.graph

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
        values. If the property has a boolean range, it returns only those
        with objects set to True.
        :param node: the instance name of a graphic object
        :return dict<string, mixed>: key is the property name, value is the
        object of the (node, p, value) triple of the ontology converted to
        its Python type
        """
        props = {}
        if node:
            for p in self.NAV_PROP:
                prop = getattr(self.NavigationDataProperty, p)
                navVal = self.getValue(node, prop)
                if navVal:
                    props[prop] = navVal.toPython()
        return props

    def getPreviousNodes(self):
        """
        Return the instance name of the previously visited graphic elements
        :return list<string>: instance name of previous graphic objects in the
        ontology according to the IS_PREVIOUS_VISITED datatype property
        """
        pPrev = self.NavigationDataProperty.IS_PREVIOUS_VISITED
        return self.getNavigationNodes(pPrev)

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
        :return list<string>: instance name of current graphic objects in the
        ontology according to the IS_CURRENT datatype property
        """
        return self.getNavigationNodes(self.NavigationDataProperty.IS_CURRENT)

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
        pCurr = self.NavigationDataProperty.IS_CURRENT
        oldCurrent = self.getNavigationNodes(pCurr)
        if oldCurrent:
            self.setNavigationNodes(
                                self.NavigationDataProperty.IS_PREVIOUS_VISITED,
                                oldCurrent)
        self.setNavigationNodes(pCurr, elms)

    def getHomeNodes(self):
        """
        Return the instance name of the currently chosen graphic elements as
        home nodes
        :return list<string>: instance names of home node graphic objects in the
        ontology according to the IS_HOME_NODE datatype property
        """
        return self.getNavigationNodes(self.NavigationDataProperty.IS_HOME_NODE)

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
        self.setNavigationNodes(self.NavigationDataProperty.IS_HOME_NODE, elms)

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
        :return string: the user-defined information for the element, an empty
        string if not found
        """
        ul = ""
        if element:
            ul = self.getValue(element,
                               self.NavigationDataProperty.HAS_USER_LABEL)
        return ul

    def setUserLabels(self, elements, userTags):
        """
        Adds the given string to the given elements as user-defined labels
        :param iterable<string> or string: a list of graphic object instance
        names or a single element name
        :param string: userTags: the user data to add to the elements. The
        string will be copied to all elements.
        """
        if elements and userTags:
            if not isinstance(elements, list):
                elements = [elements]
            p = self.NavigationDataProperty.HAS_USER_LABEL
            for e in elements:
                self.removeDataTypePropertyTriple(e, p)
                self.addDataTypePropertyTriple(e, p, userTags)

    def isLowLevelTask(self, task):
        """
        Returns whether the given task is a low-level task
        :param task: a task instance name
        :return boolean: True if the task is a low-level task, False otherwise
        """
        return self.StructuralTask.STRUCTURAL_TASK in \
                                                self.getClassOfElement(task)

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

    def classExists(self, name, ns=None):
        """
        Returns whether a class with the given name exists
        :param name: Class name
        :param ns: namespace, None for default visualization NS
        :return: True or False
        """
        return self.thingExists(name, 'entity', ns)

    def individualExists(self, name, ns=None):
        """
        Returns whether a named individual exists regardless of its class
        :param name: The individual's name
        :param ns: namespace, None for default visualization NS
        :return: True or False
        """
        return self.thingExists(name, 'instance', ns)

    def thingExists(self, name, thing_type, ns=None):
        """
        Returns whether something with the given name exists in the ontology
        :param name: The thing's name
        :param thing_type: what to search for: 'instance', 'class', 'objectProperty', 'datatypeProperty', 'property',
        or 'literal', or 'all'
        :param ns: namespace, None for default visualization NS
        :return: dict<string,string> with the types found as keys(empty dict if none). Types may be: 'literal',
        'individual', 'class', 'objectProperty', and 'datatypeProperty'. Values are the URI of the found element of the
        given type
        """
        if not ns:
            ns = self.VIS_NS
        exists = False
        typesFound = {}
        if name and (type(name) is str or type(name) is unicode):
            if thing_type in ['all', 'value', 'literal']:
                uri = self.thingOfTypeExists(name, 'literal', ns)
                if uri:
                    typesFound[o_c.OTYPE_LITERAL] = uri
            if thing_type in ['all', 'instance', 'individual']:
                uri = self.thingOfTypeExists(name, 'individual', ns)
                if uri:
                    typesFound[o_c.OTYPE_IND] = uri
            if thing_type in ['all', 'class', 'entity']:
                uri = self.thingOfTypeExists(name, 'class', ns)
                if uri:
                    typesFound[o_c.OTYPE_CLASS] = uri
            if thing_type in ['all', 'property', 'objectProperty']:
                uri = self.thingOfTypeExists(name, 'objectProperty', ns)
                if uri:
                    typesFound[o_c.OTYPE_OPROP] = uri
            if thing_type in ['all', 'property', 'datatypeProperty']:
                uri = self.thingOfTypeExists(name, 'datatypeProperty', ns)
                if uri:
                    typesFound[o_c.OTYPE_DTPROP] = uri
        return typesFound

    def contextOfLiteral(self, elementURI):
        """
        Given a literal, returns the triples where it appears in the ontology
        :param elementURI: A full URI to an existing Literal
        :return: list<(subject, predicate, object)>: triples where the given literal is the object
        """
        context = []
        for triple in self.graph.triples((None, None, elementURI)):
            context.append(triple)
        return context

    def distanceScoreOfProperty(self, name, ns=None):
        """
        Returns the distance score for the given property
        :param name: A property's name
        :param ns: namespace, None for default visualization NS
        :return:
        """
        if not ns:
            ns = self.VIS_NS
        spec = self.getValue(name, self.NavigationDataProperty.HAS_DISTANCE_SCORE,
                             default=Literal(0.0, datatype=XSD.float), ns=ns)
        return spec.toPython()

    def specificityOfElement(self, name, ns=None):
        """
        Returns the specificity score for the given element (class or property)
        :param name: Class or Property to consider
        :param ns: namespace, None for default visualization NS
        :return: float: specificity score of the element according to the "has_specificity" property
        """
        if not ns:
            ns = self.VIS_NS
        spec = self.getValue(name, self.NavigationDataProperty.HAS_SPECIFICITY,
                             default=Literal(0.0, datatype=XSD.float), ns=ns)
        return spec.toPython()

    def specificityDistanceOfClass(self, name, ns=None):
        """
        Computes the specificity distance for the given class
        :param name: Class to consider (or its URI)
        :param ns: namespace, None for default visualization NS
        :return: int: distance of class to the furthermost parent class, starting from 1
        """
        if not ns:
            ns = self.VIS_NS
        distance = 1
        max_distance = 0
        parents = self.getParentClasses(name, ns)
        for p in parents:
            p_d = self.specificityDistanceOfClass(p, ns)
            if p_d > max_distance:
                max_distance = p_d
        return distance + max_distance

    def specificityDistanceOfProperty(self, name, ns=None):
        """
        Returns the specificity distance for the given property
        :param name: Property to consider (or its URI)
        :param ns: namespace, None for default visualization NS
        :return: int: distance of property to the furthermost parent property, starting from 1
        """
        if not ns:
            ns = self.VIS_NS
        distance = 1
        max_distance = 0
        parents = self.getParentProperties(name, ns)
        for p in parents:
            p_d = self.specificityDistanceOfProperty(p, ns)
            if p_d > max_distance:
                max_distance = p_d
        return distance + max_distance

    def domainOfProperty(self, prop, stripns=True, ns=None):
        """
        Returns the entity(ies) of the domain of the given property.
        :param prop: Property to be tested
        :param stripns: boolean; whether to remove the namespace from the results
        :param ns: namespace, None for default visualization NS
        :return: List of Entity(ies) with the domain of the given property.
        """
        if not ns:
            ns = self.VIS_NS
        subjectURI = URIRef("%s#%s" % (ns, prop))
        objects = self.graph.objects(subjectURI, RDFS.domain)
        return [self.stripNamespace(s) if stripns else s for s in objects]

    def rangeOfProperty(self, prop, stripns=True, ns=None):
        """
        Returns the entity(ies) of the range of the given property.
        :param prop: Property to be tested.
        :param stripns: boolean; whether to remove the namespace from the results
        :param ns: namespace, None for default visualization NS
        :return: List of Entity(ies) with the range of the given property.
        """
        if not ns:
            ns = self.VIS_NS
        subjectURI = URIRef("%s#%s" % (ns, prop))
        objects = self.graph.objects(subjectURI, RDFS.range)
        return [self.stripNamespace(s) if stripns else s for s in objects]

    def addObjectPropertyTriple(self, s, p, o, ns = None):
        """
        Add a new object property to the ontology
        :param s: name of the subject
        :param p: name of the property
        :param o: name of the object
        :param ns: namespace, None for default visualization NS
        """
        self.addTriple(s, p, o, type="object", ns=ns)

    def addDataTypePropertyTriple(self, s, p, o, datatype=None, ns=None):
        """
        Add a new object property to the ontology
        :param s: name of the subject
        :param p: name of the property
        :param o: value of the object
        :param dataype: a valid XSD datatype for the object, if relevant
        :param ns: namespace, None for default visualization NS
        """
        self.addTriple(s, p, o, "datatype", datatype, ns)

    def addTriple(self, s, p, o, type="object", datatype=None, ns=None):
        """
        Add a new triple to the ontology
        :param s: name of the subject
        :param p: name of the property
        :param o: name or value of the object
        :param type: "object" property or "datatype" property
        :param datatype: a valid XSD datatype for the object, if relevant
        :param ns: namespace, None for default visualization NS
        """
        if not ns:
            ns = self.VIS_NS
        if not datatype:
            datatype = XSD.string
        if s and p and o:
            subjectURI = URIRef("%s#%s" % (ns, s))
            propertyURI = URIRef("%s#%s" % (ns, p))
            if type == "object":
                objectURI = URIRef("%s#%s" % (ns, o))
            else:
                objectURI = Literal(o, datatype=datatype)
            if (subjectURI, propertyURI, objectURI) not in self.graph:
                self.graph.add((subjectURI, propertyURI, objectURI))

    def removeDataTypePropertyTriple(self, s=None, p=None, o=None,
                                     datatype=None, ns=None):
        """
        Removes datatype properties from the ontology
        :param s: name of the subject
        :param p: name of the property
        :param o: name of the object
        :param dataype: a valid XSD datatype for the object, if relevant
        :param ns: namespace, None for default visualization NS
        """
        self.removeTriple(s, p, o, "datatype", datatype, ns)

    def removeObjectPropertyTriple(self, s=None, p=None, o=None, ns=None):
        """
        Removes object properties from the ontology
        :param s: name of the subject
        :param p: name of the property
        :param o: name of the object
        :param ns: namespace, None for default visualization NS
        """
        self.removeTriple(s, p, o, ns=ns)

    def removeTriple(self, s=None, p=None, o=None, type="object",
                                     datatype = None, ns=None):
        """
        Removes triples from the ontology.
        :param s: name of the subject; None to remove all matching triples.
        :param p: name of the property; None to remove all matching triples.
        :param o: name or value of the object; None to remove all matching.
        :param type: "object" property or "datatype" property
        :param datatype: a valid XSD datatype for the object, if relevant
        :param ns: namespace, None for default visualization NS
        """
        if not ns:
            ns = self.VIS_NS
        allNone = True
        if s is not None:
            allNone = False
            s = URIRef("%s#%s" % (ns, s))
        if p is not None:
            allNone = False
            p = URIRef("%s#%s" % (ns, p))
        if o is not None:
            allNone = False
            if type == 'datatype':
                if datatype is None:
                    datatype = XSD.string
                o = Literal(o, datatype=datatype)
            else:
                o = URIRef("%s#%s" % (ns, o))
        if not allNone:
            self.graph.remove((s, p, o))

    def tripleExists(self, s, p, o, type="object", ns=None):
        """
        Returns whether a given triple exists
        :param s: name of the triple's subject
        :param p: name of the triple's property
        :param o: name or value of the triple's object
        :param type: "object" property or "datatype" property
        :param ns: namespace, None for default visualization NS
        """
        exists = False
        if not ns:
            ns = self.VIS_NS
        if s and p and o:
            subjectURI = URIRef("%s#%s" % (ns, s))
            propertyURI = URIRef("%s#%s" % (ns, p))
            if type == "object":
                objectURI = URIRef("%s#%s" % (ns, o))
            else:
                objectURI = Literal(o)
            exists = (subjectURI, propertyURI, objectURI) in self.graph
        return exists

    def addProperty(self, propertyName, type, ns=None):
        """
        Adds a new property to the ontology (n.b. NOT a property occurrence)
        :param propertyName: Name of the property to be added
        :param type: Type of the property ("object" or "datatype")
        :param ns: namespace, None for default visualization NS
        """
        if not ns:
            ns = self.VIS_NS
        if not self.hasProperty(propertyName, type, ns):
            objectURI = URIRef("%s#%s" % (ns, propertyName))
            dataPropertyURI = URIRef("%s#type" % c.RDF_NS)
            if type == "object":
                subjectURI = URIRef("%s#ObjectProperty" % c.OWL_NS)
            else:
                subjectURI = URIRef("%s#DatatypeProperty" % c.OWL_NS)
            self.graph.add((objectURI, dataPropertyURI, subjectURI))

    def hasProperty(self, propertyName, type, ns=None):
        """
        Check whether a property exists in the ontology.
        :param propertyName: Name of the property to be tested
        :param type: Type of the property ("object" or "datatype")
        :param ns: namespace, None for default visualization NS
        :return: 'True' if the property with propertyName exists
            in the ontology, 'False' otherwise
        """
        if not ns:
            ns = self.VIS_NS
        objectURI = URIRef("%s#%s" % (ns, propertyName))
        dataPropertyURI = URIRef("%s#type" % c.RDF_NS)
        if type == "object":
            subjectURI = URIRef("%s#ObjectProperty" % c.OWL_NS)
        else:
            subjectURI = URIRef("%s#DatatypeProperty" % c.OWL_NS)
        return (objectURI, dataPropertyURI, subjectURI) in self.graph

    def stripNamespace(self, item):
        """
        Returns the name of the given item without the namespace prefix
        :param item: an instance's name, with a NS prefix appended
        :return string: the name without the NS prefix
        """
        if item and '#' in item:
            return item.split('#')[1]
        return item

    def getNamespace(self, uri):
        """
        Returns the namespace of the given URI
        :param item: an element's URI
        :return: The namespace part of the URI
        """
        ns = ''
        if uri and '#' in uri:
            return uri.split('#')[0]
        return ns

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
                elif normItem.lower() in c.NavFilters: # Navigation Filters
                    normItem = c.NavFilters[normItem.lower()]
                else:
                    normItem = normItem.replace('_', ' ')
            else:
                normItem = s
        else:
            normItem = ""
        return normItem


    def thingOfTypeExists(self, name, subjectType, ns):
        """
        Returns whether something of the given type exists in the ontology. Matches are looked up in order:
            1. Exact name as given (whitespace replaced by underscore)
            2. Lowercase
            3. Uppercase first letter for non-properties
        :param name: The name of the thing to search for
        :param subjectType: 'literal', 'individual', 'class', 'objectProperty', or 'datatypeProperty'
        :param ns: A namespace, None for default
        :return: Found element's URI if exists, False otherwise
        """
        if not ns:
            ns = self.VIS_NS
        if subjectType == 'literal':
            elementURI = Literal(name.replace(' ', '_'))
            exists = (None, None, elementURI) in self.graph
            if not exists:
                elementURI = Literal(name.lower().replace(' ', '_'))
                exists = (None, None, elementURI) in self.graph
            if not exists:
                elementURI = Literal(stringToID(name, subjectType))
                exists = (None, None, elementURI) in self.graph
        else:
            if subjectType == 'individual':
                o_uri = URIRef("%s#%s" % (c.OWL_NS, "NamedIndividual"))
            elif subjectType == 'class':
                o_uri = URIRef("%s#%s" % (c.OWL_NS, "Class"))
            elif subjectType == 'objectProperty':
                o_uri = URIRef("%s#%s" % (c.OWL_NS, "ObjectProperty"))
            elif subjectType == 'datatypeProperty':
                o_uri = URIRef("%s#%s" % (c.OWL_NS, "DatatypeProperty"))
            else:
                raise ValueError('thingOfTypeExists: invalid type %s' % subjectType)
            # Try string as-is firstly
            elementURI = URIRef("%s#%s" % (ns, name.replace(' ', '_')))
            exists = (elementURI, RDF.type, o_uri) in self.graph
            if not exists:
                # Try lowercase
                elementURI = URIRef("%s#%s" % (ns, name.lower().replace(' ', '_')))
                exists = (elementURI, RDF.type, o_uri) in self.graph
                if not exists:
                    # Try ontology format
                    name_norm = stringToID(name, subjectType)
                    elementURI = URIRef("%s#%s" % (ns, name_norm))
                    exists = (elementURI, RDF.type, o_uri) in self.graph
        return elementURI if exists else False

    def computeSpecificities(self, items=None, type='class'):
        """
        Computes the specificity score of all classes or properties in the ontology
        :param items: items to consider, None to fetch all.
        :param type: type of the items; 'class' or 'property'
        :return: None, updates the serialized ontology
        """
        self.addProperty(self.NavigationDataProperty.HAS_SPECIFICITY, 'datatype')
        distances = {}
        if not items:
            if type == 'class':
                items = self.getClasses()
            elif type == 'property':
                items = self.getProperties()
            else:
                raise ValueError('computeSpecificities: invalid type %s.' % type)
        max_spec = 0
        for i in items:
            if type == 'class':
                s = self.specificityDistanceOfClass(i) - 1
            else:
                s = self.specificityDistanceOfProperty(i) - 1
            distances[i] = s
            if s > max_spec:
                max_spec = s
        max_spec = float(max_spec)
        for i, s in distances.iteritems():
            s = float(s)
            self.addDataTypePropertyTriple(self.stripNamespace(i),
                                           self.NavigationDataProperty.HAS_SPECIFICITY,
                                           s/max_spec, XSD.float)

    def computeDistanceScores(self, props=None):
        """
        Computes the distance scores of all properties in the ontology
        :param props: properties to consider, None to fetch all.
        :return: None, updates the serialized ontology
        """
        self.addProperty(self.NavigationDataProperty.HAS_DISTANCE_SCORE, 'datatype')
        if not props:
            props = self.getProperties()
        for p in props:
            specs = []
            dom = self.domainOfProperty(self.stripNamespace(p), stripns=False, ns=self.getNamespace(p))
            ran = self.rangeOfProperty(self.stripNamespace(p), stripns=False, ns=self.getNamespace(p))
            specs.extend([self.specificityOfElement(self.stripNamespace(d), ns=self.getNamespace(d)) for d in dom])
            specs.extend([self.specificityOfElement(self.stripNamespace(r), ns=self.getNamespace(r)) for r in ran])
            avg = 0.0
            if specs:
                avg = float(sum(specs)) / float(len(specs))
            self.addDataTypePropertyTriple(self.stripNamespace(p),
                                           self.NavigationDataProperty.HAS_DISTANCE_SCORE,
                                           avg, XSD.float)

    def __resetNavigation(self):
        """
        Recomputes properties useful for navigation of the graphic:
        1. Specificity scores of classes and properties
        2. Distance scores of properties
        :return: None, updates the serialized ontology
        """
        self.removeDataTypePropertyTriple(None, self.NavigationDataProperty.HAS_SPECIFICITY, None)
        self.computeSpecificities('class')
        all_props = self.getProperties()
        self.computeSpecificities(all_props, 'property')
        self.removeDataTypePropertyTriple(None, self.NavigationDataProperty.HAS_DISTANCE_SCORE, None)
        self.computeDistanceScores(all_props)
