import rdflib
from rdflib.term import URIRef
from rdflib import RDF, RDFS, OWL, Namespace, Literal, XSD
from util import *
import os
import bsddb
import const as c
import constants as o_c


class UpperOntology(object):
    """
    Upper Ontology handler; contains common attributes and methods for handling RDF ontologies
    """
    def __init__(self, RDFpath):
        """
        UpperOntology constructor
        :param RDFpath: string; path to an RDF ontology file
        """
        self.VIS_NS = c.VIS_NS
        self.graph = rdflib.ConjunctiveGraph("Sleepycat")
        if not os.path.isdir(c.STOREDIR):
            os.makedirs(c.STOREDIR)
        self.open(c.STOREDIR)
        if not self.graph and RDFpath is not None:
            self.load(RDFpath)

    class ScoreDataProperty:
        """
        Datatype Properties that define scores for resources
        """
        HAS_SPECIFICITY = "has_specificity"
        HAS_DISTANCE_SCORE = "has_distance_score"
        HAS_PROP_FINAL_SCORE = "has_property_final_score"

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
        Returns the number of instances of the given resource
        """
        c = 0
        if element:
            norm = self.normalizeItem(element)
            c = len(set(self.getInstances(norm)))
        return c

    def executeQuery(self, sparql):
        """
        Execute the given SPARQL query against the ontology
        :return: list<string>: a list of result rows
        """
        res = []
        if sparql:
            query_res = self.graph.query(sparql)
            res = [row for row in query_res]
        return res

    def getNamespaces(self):
        """
        Returns all namespaces in the loaded ontology
        :return: List<tuple<string (NS prefix); string (NS URI)>>
        """
        from const import VIS_NS
        vis_uri = "%s#" % VIS_NS
        ns_with_prefixes = []
        #  Use preferred NS prefixes instead of default ones
        common_prefixes = {'http://www.w3.org/1999/02/22-rdf-syntax-ns#': 'rdf',
                           'http://www.w3.org/2000/01/rdf-schema#': 'rdfs',
                           'http://www.w3.org/2002/07/owl#': 'owl',
                           'http://www.w3.org/XML/1998/namespace#': 'xml',
                           'http://www.w3.org/2001/XMLSchema#': 'xsd',
                           vis_uri: 'vis'}
        if self.graph:
            all_ns = [(p, str(u)) for p, u in self.graph.namespace_manager.namespaces()]
            for p, uri in all_ns:
                prefix = common_prefixes.get(uri)
                if not prefix:
                    prefix = p
                ns_with_prefixes.append((prefix, uri))
        return ns_with_prefixes

    def yieldResource(self, res_type='all', ns='all'):
        """
        Yield a new URI of the given type each time
        :param res_type: 'class', 'individual', 'property', 'objectProperty', 'datatypeProperty', or 'all'. The kind
        of resource to consider.
        :param ns: namespaces to consider (string or list), 'all' for all
        :return: generator of (URI, type) string tuples
        """
        dtype_uri = URIRef("%s#%s" % (c.OWL_NS, "DatatypeProperty"))
        object_uri = URIRef("%s#%s" % (c.OWL_NS, "ObjectProperty"))
        class_uri = URIRef("%s#%s" % (c.OWL_NS, "Class"))
        ind_uri = URIRef("%s#%s" % (c.OWL_NS, "NamedIndividual"))
        for s, p, o in self.graph.triples((None, RDF.type, None)):
            if o == object_uri and res_type in ['object', 'property', 'all']:
                if ns == 'all' or self.getNamespace(s) == ns:
                    yield str(s), "objectProperty"
            elif o == dtype_uri and res_type in ['datatype', 'property', 'all']:
                if ns == 'all' or self.getNamespace(s) == ns:
                    yield str(s), "datatypeProperty"
            elif o == class_uri and res_type in ['class', 'entity', 'all']:
                if ns == 'all' or self.getNamespace(s) == ns:
                    yield str(s), "class"
            elif o == ind_uri and res_type in ['individual', 'instance', 'all']:
                if ns == 'all' or self.getNamespace(s) == ns:
                    yield str(s), "individual"

    def getClasses(self, ns='all'):
        """
        Returns all classes in the ontology
        :param ns: namespaces to consider (string or list), 'all' for all
        :return: list<string>: a list of class URIs
        """
        if not ns:
            ns = self.VIS_NS
        classes = [str(i) for i in self.graph.subjects(RDF.type, URIRef("%s#%s" % (c.OWL_NS, "Class")))]
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
            props = [str(i) for i in self.graph.subjects(RDF.type,
                                                      URIRef("%s#%s" % (c.OWL_NS, "ObjectProperty")))]
        dtype_prop = []
        if prop_type in ['all', 'datatype']:
            dtype_prop = [str(i) for i in self.graph.subjects(RDF.type,
                                                      URIRef("%s#%s" % (c.OWL_NS, "DatatypeProperty")))]
        props.extend(dtype_prop)
        if ns == 'all':
            return props
        else:
            if not isinstance(ns, list):
                ns = [ns]
            return [i for i in props if self.getNamespace(i) in ns]

    def getInstances(self, entityName='all', stripns=True, ns=None, limit=100):
        """
        Returns a list of instances of the given class
        :param entityName: name or URI of a class in the ontology, 'all' to get all individuals regardless of class
        :param stripns: True to strip the namespace from the output (default), False otherwise
        :param ns: namespaces to consider (string or list), 'all' for all
        :param limit: int; maximum number of instances to return; zero for all
        :return list<string>: a list of instance names or URIs, depending on the stripns parameter
        """
        if not ns:
            ns = self.getNamespace(entityName)
            if not ns:
                ns = self.VIS_NS
        instances = []
        if self.graph and entityName:
            i = 0
            namedIndividualURI = URIRef("%s#%s" % (c.OWL_NS, "NamedIndividual"))
            if entityName != 'all':
                name = self.stripNamespace(entityName)
                entityURI = URIRef("%s#%s" % (ns, name))
                for instance in self.graph.subjects(RDF.type, entityURI):
                    if (instance, RDF.type, namedIndividualURI) in self.graph:
                        instances.append(instance)
                        i += 1
                        if i == limit:
                            break
            else:
                if ns != 'all' and not isinstance(ns, list):
                    ns = [ns]
                else:
                    ns = None
                for j in self.graph.subjects(RDF.type, namedIndividualURI):
                    j_ns = self.getNamespace(j) if ns else None
                    if not j_ns or j_ns in ns:
                        instances.append(str(j))
                        i += 1
                        if i == limit:
                            break
        if stripns:
            return [self.stripNamespace(i) for i in instances]
        else:
            return instances

    def generateInstances(self, entityName='all', stripns=True, ns=None):
        """
        Dynamically generate instances of the given class
        :param entityName: name or URI of a class in the ontology, 'all' to get all individuals regardless of class
        :param stripns: True to strip the namespace from the output (default), False otherwise
        :param ns: namespaces to consider (string or list), 'all' for all
        :return: A generator with instance names or URIs depending on :stripns
        """
        if not ns:
            ns = self.getNamespace(entityName)
            if not ns:
                ns = self.VIS_NS
        if self.graph and entityName:
            namedIndividualURI = URIRef("%s#%s" % (c.OWL_NS, "NamedIndividual"))
            if entityName != 'all':
                name = self.stripNamespace(entityName)
                entityURI = URIRef("%s#%s" % (ns, name))
                for instance in self.graph.subjects(RDF.type, entityURI):
                    if (instance, RDF.type, namedIndividualURI) in self.graph:
                        yield self.stripNamespace(instance) if stripns else instance
            else:
                if ns != 'all' and not isinstance(ns, list):
                    ns = [ns]
                else:
                    ns = None
                for instance in self.graph.subjects(RDF.type, namedIndividualURI):
                    j_ns = self.getNamespace(instance) if ns else None
                    if not j_ns or j_ns in ns:
                        yield self.stripNamespace(instance) if stripns else instance

    def getOccurrences(self, property, stripns=True, ns=None, limit=100):
        """
        Returns a list of occurrences of the given property
        :param property: name or URI of a property in the ontology
        :param stripns: True to strip namespaces from the output (default), False otherwise
        :param ns: namespaces to consider (string or list), 'all' for all
        :param limit: int; maximum number of occurrences to return
        :return list<(string, string, string)>: a list of triples where the given property takes part
        """
        if not ns:
            ns = self.getNamespace(property)
            if not ns:
                ns = self.VIS_NS
        p_name = self.stripNamespace(property)
        propertyURI = URIRef("%s#%s" % (ns, p_name))
        triples = []
        n = 0
        for s, p, o in self.graph.triples((None, propertyURI, None)):
            n += 1
            if n > limit:
                break
            if stripns:
                triples.append((self.stripNamespace(s), self.stripNamespace(p), self.stripNamespace(o)))
            else:
                triples.append((str(s), str(p), str(o)))
        return triples

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
                    ns=None, stripns=True):
        """
        Returns a list with all subjects for a given property, object pair
        """
        if not ns and propertyType == 'object':
            ns = self.getNamespace(obj)
            if not ns:
                ns = self.VIS_NS
        prop_ns = self.getNamespace(property)
        if not prop_ns:
            prop_ns = self.VIS_NS
        subjects = []
        if self.graph and property and obj:
            propertyURI = URIRef("%s#%s" % (prop_ns, self.stripNamespace(property)))
            if propertyType == 'datatype':
                if not dtype:
                    objectURI = Literal(obj)
                else:
                    objectURI = Literal(obj, datatype=dtype)
            else:
                objectURI = URIRef("%s#%s" % (ns, self.stripNamespace(obj)))
            subjects = self.graph.subjects(propertyURI, objectURI)
        if stripns:
            return map(self.stripNamespace, subjects)
        else:
            return [str(s) for s in subjects]

    def getObjects(self, subj, property, ns=None, stripns=True):
        """
        Returns a list with all objects for a given subject, property pair
        """
        if not ns:
            ns = self.getNamespace(subj)
            if not ns:
                ns = self.VIS_NS
        prop_ns = self.getNamespace(property)
        if not prop_ns:
            prop_ns = self.VIS_NS
        objects = []
        if self.graph and property and subj:
            propertyURI = URIRef("%s#%s" % (prop_ns, self.stripNamespace(property)))
            subjectURI = URIRef("%s#%s" % (ns, self.stripNamespace(subj)))
            objects = self.graph.objects(subjectURI, propertyURI)
        if stripns:
            return map(self.stripNamespace, objects)
        else:
            return [str(o) for o in objects]

    def getValue(self, s, p, default=None, ns=None, stripns=True):
        """
        Returns the value of a functional property. An exception is raised
        if more than one (s, p, _) triples are found
        :param s: name or URI of the subject
        :param p: name or URI of the (functional) property
        :param default: default value to use if nothing found
        :param ns: namespace, None for default visualization NS
        :param stripns: boolean; whether to remove the namespace from the results
        """
        if not ns:
            ns = self.getNamespace(s)
            if not ns:
                ns = self.VIS_NS
            p_ns = self.getNamespace(p)
            if not p_ns:
                p_ns = self.VIS_NS
        else:
            p_ns = ns
        val = None
        if s and p:
            subjectURI = URIRef("%s#%s" % (ns, self.stripNamespace(s)))
            propertyURI = URIRef("%s#%s" % (p_ns, self.stripNamespace(p)))
            val = self.graph.value(subjectURI, propertyURI, default=default)
        if not val:
            return ''
        else:
            return self.stripNamespace(str(val)) if stripns else val.toPython()

    def getClassOfElement(self, element, stripns=True, ns=None):
        """
        Return the Entities an individual belongs to; an empty list if none found
        :param element: and instace name or uri
        :param stripns: boolean; whether to remove the namespace from the results
        :param ns: namespace, None for default visualization NS
        :return: a list with the names of the classes the element belongs to
        """
        classes = []
        if not ns:
            ns = self.getNamespace(element)
            if not ns:
                ns = self.VIS_NS
        element = self.stripNamespace(element)
        if element:
            subjectURI = URIRef("%s#%s" % (ns, element))
            propertyURI = URIRef("%s#type" % c.RDF_NS)
            objects = self.graph.objects(subjectURI, propertyURI)
            namedIndividualURI = URIRef("%s#%s" % (c.OWL_NS, "NamedIndividual"))
            if stripns:
                classes = [self.stripNamespace(o) for o in objects if o != namedIndividualURI]
            else:
                classes = [str(o) for o in objects if o != namedIndividualURI]
        return classes

    def getTopElements(self, child, elem_type='class', ns=None, depth=-1):
        """
        Returns the most generic parent element (class or property) of the given child
        :param child: The name of the child class or property
        :param elem_type: ontology resource type of element: 'class' or 'property'
        :param ns: namespace, None for default visualization NS
        :param int: current depth level of search
        :return: list<string>: the URIs of the topmost parent elements (usually just one)
        """
        if child:
            if elem_type == 'class':
                parents = self.getParentClasses(child, ns, stripns=False)
            elif elem_type == 'property':
                parents = self.getParentProperties(child, ns, stripns=False)
            else:
                parents = []
            max_parent_depth = -1
            topclasses = [child]
            depth += 1
            for c in parents:
                next_classes, next_depth = self.getTopElements(c, elem_type, ns, depth)
                if next_depth > max_parent_depth:
                    max_parent_depth = next_depth
                    topclasses = next_classes
                    depth = max_parent_depth + 1
                elif next_depth == max_parent_depth:
                    topclasses.extend(next_classes)
        else:
            topclasses = []
        return topclasses, depth

    def getSubclasses(self, parentClass, ns=None):
        """
        Returns all subclasses for the parent class.
        :param parentClass: The name or URI of the parent class
        :param ns: namespace, None for default visualization NS
        :return: List<string> its subclasses
        """
        if not ns:
            ns = self.getNamespace(parentClass)
            if not ns:
                ns = self.VIS_NS
        namedIndividualURI = URIRef("%s#%s" % (c.OWL_NS, "NamedIndividual"))
        propertyURI = URIRef("%s#subClassOf" % c.RDFS_NS)
        objectURI = URIRef("%s#%s" % (ns, self.stripNamespace(parentClass)))
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
            ns = self.getNamespace(childClass)
            if not ns:
                ns = self.VIS_NS
        namedIndividualURI = URIRef("%s#%s" % (c.OWL_NS, "NamedIndividual"))
        propertyURI = URIRef("%s#subClassOf" % c.RDFS_NS)
        subjectURI = URIRef("%s#%s" % (ns, self.stripNamespace(childClass)))
        objects = self.graph.objects(subjectURI, propertyURI)
        if stripns:
            classes = [self.stripNamespace(o) for o in objects
                       if o != namedIndividualURI and not isinstance(o, rdflib.BNode)]
        else:
            classes = [str(o) for o in objects if o != namedIndividualURI and not isinstance(o, rdflib.BNode)]
        return classes

    def getParentProperties(self, childProp, ns=None, stripns=True):
        """
        Returns all parent properties for the given property.
        :param childProp: The name or URI of the child property
        :param ns: namespace, None for default visualization NS
        :param stripns: True to strip the namespace from the output (default), False otherwise
        :return: List<string> its parent classes
        """
        if not ns:
            ns = self.getNamespace(childProp)
            if not ns:
                ns = self.VIS_NS
        propertyURI = URIRef("%s#subPropertyOf" % c.RDFS_NS)
        subjectURI = URIRef("%s#%s" % (ns, self.stripNamespace(childProp)))
        objects = self.graph.objects(subjectURI, propertyURI)
        if stripns:
            return [self.stripNamespace(o) for o in objects]
        else:
            return [str(o) for o in objects]

    def instanceIsOfClass(self, instance, entity, ns=None):
        """
        Returns whether the given individual is of the given class
        :param instance: The name of the individual
        :param entity: The name of a class
        :param ns: instance and class namespace, None for default visualization NS
        :return: True if 'instance' is of type 'class'
        """
        if not ns:
            ns = self.getNamespace(instance)
            if not ns:
                ns = self.VIS_NS
            class_ns = self.getNamespace(entity)
            if not class_ns:
                class_ns = self.VIS_NS
        else:
            class_ns = ns
        namedIndividualURI = URIRef("%s#%s" % (c.OWL_NS, "NamedIndividual"))
        subjectURI = URIRef("%s#%s" % (ns, self.stripNamespace(instance)))
        propertyURI = URIRef("%s#type" % c.RDF_NS)
        objectURI = URIRef("%s#%s" % (class_ns, self.stripNamespace(entity)))
        return (subjectURI, propertyURI, namedIndividualURI) in self.graph and \
               (subjectURI, propertyURI, objectURI) in self.graph

    def getRDFLabel(self, element, stripns=True):
        """
        Returns the RDF labels of the given element, if it exists
        :param element: A resource URI or name
        :param stripns: boolean; whether to remove the namespace from the results
        :return: list<string>; label values or URIs for the given element, empty if none found
        """
        return self.getObjects(element, RDFS.label, stripns=stripns)

    def classExists(self, name, ns=None):
        """
        Returns whether a class with the given name exists
        :param name: Class name
        :param ns: namespace, None for default visualization NS
        :return: True or False
        """
        return self.thingExists(name, 'entity', ns)

    def propertyExists(self, name, type='all', ns=None):
        """
        Returns whether a property with the given name exists
        :param name: property name
        :param type: type of property: 'objectProperty', 'datatypeProperty', or 'all' (default)
        :param ns: namespace, None for default visualization NS
        :return: True or False
        """
        exists = False
        if type in ['objectProperty', 'all']:
            exists = self.thingOfTypeExists(name, 'objectProperty', ns)
        if not exists and type in ['datatypeProperty', 'all']:
            exists = self.thingOfTypeExists(name, 'datatypeProperty', ns)
        return exists

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
        :param name: The thing's name or URI
        :param thing_type: what to search for: 'instance', 'class', 'objectProperty', 'datatypeProperty', 'property',
        or 'literal', or 'all'
        :param ns: namespace, None for default visualization NS
        :return: dict<string,string> with the types found as keys(empty dict if none). Types may be: 'literal',
        'individual', 'class', 'objectProperty', and 'datatypeProperty'. Values are the URI of the found element of the
        given type
        """
        if not ns:
            ns = self.getNamespace(name)
            if not ns:
                ns = self.VIS_NS
        exists = False
        typesFound = {}
        if name and isinstance(name, basestring):
            name = self.stripNamespace(name)
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
        :param elementURI: Literal value
        :return: list<(subject, predicate, object)>: triples where the given literal is the object
        """
        context = []
        for s, p, o in self.graph.triples((None, None, Literal(elementURI))):
            context.append((str(s), str(p), str(o)))
        return context

    def distanceScoreOfProperty(self, name, ns=None):
        """
        Returns the distance score for the given property
        :param name: A property's name
        :param ns: namespace, None for default visualization NS
        :return:
        """
        if not ns:
            ns = self.getNamespace(name)
            if not ns:
                ns = self.VIS_NS
        spec = self.getValue(self.stripNamespace(name), self.ScoreDataProperty.HAS_DISTANCE_SCORE,
                             default=Literal(0.0, datatype=XSD.float), ns=ns)
        return float(spec) if spec else 0.0

    def specificityOfElement(self, name, ns=None):
        """
        Returns the specificity score for the given element (class or property)
        :param name: Class or Property to consider
        :param ns: namespace, None for default visualization NS
        :return: float: specificity score of the element according to the "has_specificity" property
        """
        if not ns:
            ns = self.getNamespace(name)
            if not ns:
                ns = self.VIS_NS
        spec = self.getValue(self.stripNamespace(name), self.ScoreDataProperty.HAS_SPECIFICITY,
                             default=Literal(0.0, datatype=XSD.float), ns=ns)
        return float(spec) if spec else 0.0

    def specificityDistanceOfClass(self, name, ns=None):
        """
        Computes the specificity distance for the given class
        :param name: Class to consider (or its URI)
        :param ns: namespace, None for default visualization NS
        :return: int: distance of class to the furthermost parent class, starting from 1
        """
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
            ns = self.getNamespace(prop)
            if not ns:
                ns = self.VIS_NS
        prop = self.stripNamespace(prop)
        subjectURI = URIRef("%s#%s" % (ns, prop))
        objects = self.graph.objects(subjectURI, RDFS.domain)
        return [self.stripNamespace(s) if stripns else str(s) for s in objects]

    def rangeOfProperty(self, prop, stripns=True, ns=None):
        """
        Returns the entity(ies) of the range of the given property.
        :param prop: Property to be tested.
        :param stripns: boolean; whether to remove the namespace from the results
        :param ns: namespace, None for default visualization NS
        :return: List of Entity(ies) with the range of the given property.
        """
        if not ns:
            ns = self.getNamespace(prop)
            if not ns:
                ns = self.VIS_NS
        prop = self.stripNamespace(prop)
        subjectURI = URIRef("%s#%s" % (ns, prop))
        objects = self.graph.objects(subjectURI, RDFS.range)
        return [self.stripNamespace(s) if stripns else str(s) for s in objects]

    def propertiesWithRangeOrDomain(self, element, range_or_domain, stripns=True):
        """
        Returns the properties having the given class as a member of their range or domain
        :param element: URI of the class to be considered
        :param range_or_domain: 'range' or 'domain' depending on what needs to be returned
        :param stripns: boolean; whether to remove the namespace from the results
        :return: List of object properties with @element in their range
        """
        ns = self.getNamespace(element)
        if not ns:
            ns = self.VIS_NS
        if range_or_domain == 'domain':
            prop = RDFS.domain
        elif range_or_domain == 'range':
            prop = RDFS.range
        else:
            return []
        objectURI = URIRef("%s#%s" % (ns, self.stripNamespace(element)))
        subjects = self.graph.subjects(prop, objectURI)
        if stripns:
            return map(self.stripNamespace, subjects)
        else:
            return [str(s) for s in subjects]

    def propertiesWithoutRangeOrDomain(self, type='object', range_or_domain='both', stripns=True):
        """
        Returns the properties without any specified range or domain
        :param type: string; type of property to consider: 'object' or 'datatype' properties.
        :param range_or_domain: 'range', 'domain', or 'both'
        :param stripns: boolean; whether to remove the namespace from the results or return full URIs
        :return: List<string>: property names or URIs
        """
        query = """prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
                   prefix owl: <http://www.w3.org/2002/07/owl#> 
                   select ?p where {
                   """
        if type == 'datatype':
            query += "?p a owl:DatatypeProperty\n"
        elif type == 'object':
            query += "?p a owl:ObjectProperty\n"
        if range_or_domain in ['domain', 'both']:
            query += """filter not exists {
                        ?p rdfs:domain ?dom
                        }
                        """
        if range_or_domain in ['range', 'both']:
            query += """filter not exists {
                        ?p rdfs:range ?ran
                        }
                        """
        query += "}"
        query_res = self.graph.query(query)
        return [self.stripNamespace(row.p) if stripns else row.p for row in query_res]

    def neighborRangeOrDomainClasses(self, element, range_or_domain, stripns=True):
        """
        Return the neighbor classes of the given one according to the domain or range of the properties in the
        ontology. For each property in the ontology, if the class belongs to a propery's domain, the classes on the
        property's range are returned. Similarly, if the class belongs to a propery's range, the classes on its domain
        are returned.
        :param element: URI of the class to be considered
        :param range_or_domain: 'range' or 'domain' depending on whether :element must belong to the properties' range
        or domain, respectively.
        :param stripns: boolean; whether to remove the namespace from the results
        :return: List of neighbor classes for :element.
        """
        neighbors = set()
        props = self.propertiesWithRangeOrDomain(element, range_or_domain, stripns=False)
        for p in props:
            if range_or_domain == 'range':
                neighbors.update(self.domainOfProperty(self.stripNamespace(p), False, self.getNamespace(p)))
            else:
                neighbors.update(self.rangeOfProperty(self.stripNamespace(p), False, self.getNamespace(p)))
        if stripns:
            neighbors_list = [self.stripNamespace(e) for e in neighbors]
        else:
            neighbors_list = list(neighbors)
        return neighbors_list

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
            s_ns = self.getNamespace(s)
            p_ns = self.getNamespace(p)
            o_ns = self.getNamespace(o)
            if not s_ns:
                s_ns = ns
            if not p_ns:
                p_ns = ns
            if not o_ns:
                o_ns = ns
        else:
            s_ns, p_ns, o_ns = ns, ns, ns
        if s and p and o:
            subjectURI = URIRef("%s#%s" % (s_ns, self.stripNamespace(s)))
            propertyURI = URIRef("%s#%s" % (p_ns, self.stripNamespace(p)))
            if type == "object":
                objectURI = URIRef("%s#%s" % (o_ns, self.stripNamespace(o)))
            else:
                objectURI = Literal(self.stripNamespace(o))
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
            ns = self.getNamespace(propertyName)
            if not ns:
                ns = self.VIS_NS
        if not self.hasProperty(propertyName, type, ns):
            objectURI = URIRef("%s#%s" % (ns, self.stripNamespace(propertyName)))
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
            ns = self.getNamespace(propertyName)
            if not ns:
                ns = self.VIS_NS
        objectURI = URIRef("%s#%s" % (ns, self.stripNamespace(propertyName)))
        dataPropertyURI = URIRef("%s#type" % c.RDF_NS)
        if type == "object":
            subjectURI = URIRef("%s#ObjectProperty" % c.OWL_NS)
        else:
            subjectURI = URIRef("%s#DatatypeProperty" % c.OWL_NS)
        return (objectURI, dataPropertyURI, subjectURI) in self.graph

    @staticmethod
    def stripNamespace(uri):
        """
        Returns the name of the given item without the namespace prefix
        :param uri: an instance's URI
        :return string: resource name without NS prefix
        """
        if uri:
            if '#' in uri:
                return uri.split('#')[1]
            else:
                return str(uri)
        return uri

    @staticmethod
    def getNamespace(uri):
        """
        Returns the namespace of the given URI
        :param item: an element's URI
        :return: The namespace part of the URI
        """
        ns = ''
        if uri and '#' in uri:
            return uri.split('#')[0]
        return ns

    def normalizeItem(self, item, type='entity'):
        """
        Normalizes the name of a given Entity or Property.
        Entities are capitalized, properties are not.
        """
        if item:
            s = item.replace(' ', '_')
            if type == 'entity':
                normItem = '_'.join(word[0].upper() + word[1:].lower()
                                for word in s.split('_'))
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
            ns = self.getNamespace(name)
            if not ns:
                ns = self.VIS_NS
        name = self.stripNamespace(name)
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
        return str(elementURI) if exists else False

    def computeSpecificities(self, items=None, type='class'):
        """
        Computes the specificity score of all classes or properties in the ontology
        :param items: items to consider, None to fetch all.
        :param type: type of the items; 'class' or 'property'
        :return: None, updates the serialized ontology
        """
        self.addProperty(self.ScoreDataProperty.HAS_SPECIFICITY, 'datatype')
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
                                           self.ScoreDataProperty.HAS_SPECIFICITY,
                                           s/max_spec, XSD.float)

    def computeDistanceScores(self, props=None):
        """
        Computes the distance scores of all properties in the ontology
        :param props: properties to consider, None to fetch all.
        :return: None, updates the serialized ontology
        """
        self.addProperty(self.ScoreDataProperty.HAS_DISTANCE_SCORE, 'datatype')
        from const import XSD_NS, XML_NS
        if not props:
            props = self.getProperties()
        for p in props:
            specs = []
            dom = self.domainOfProperty(self.stripNamespace(p), stripns=False, ns=self.getNamespace(p))
            ran = self.rangeOfProperty(self.stripNamespace(p), stripns=False, ns=self.getNamespace(p))
            for d in dom:
                d_ns = self.getNamespace(d)
                if d_ns and d_ns not in [XML_NS, XSD_NS]:
                    specs.append(self.specificityOfElement(d, ns=d_ns))
            for r in ran:
                r_ns = self.getNamespace(r)
                if r_ns and r_ns not in [XML_NS, XSD_NS]:
                    specs.append(self.specificityOfElement(r, ns=r_ns))
            avg = 0.0
            if specs:
                avg = float(sum(specs)) / float(len(specs))
            self.addDataTypePropertyTriple(self.stripNamespace(p),
                                           self.ScoreDataProperty.HAS_DISTANCE_SCORE,
                                           avg, XSD.float)

    def resetNavigation(self):
        """
        Recomputes properties useful for navigation of the graphic:
        1. Specificity scores of classes and properties
        2. Distance scores of properties
        :return: None, updates the serialized ontology
        """
        self.removeDataTypePropertyTriple(None, self.ScoreDataProperty.HAS_SPECIFICITY, None)
        self.computeSpecificities([], 'class')
        all_props = self.getProperties()
        self.computeSpecificities(all_props, 'property')
        self.removeDataTypePropertyTriple(None, self.ScoreDataProperty.HAS_DISTANCE_SCORE, None)
        self.computeDistanceScores(all_props)
