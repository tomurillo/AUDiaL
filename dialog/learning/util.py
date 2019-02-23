from NLP.model.OE import *
from dialog.model.LearningVote import *
from dialog.model.SuggestionPair import *
from dialog.model.Key import *
from dialog.learning.config import *

def getGenericElement(element, o):
    """
    Returns the URI of a given element's generic element
    1. If element is a class or property, return the URI of its generic parent class/prop. (if it exists)
    2. If element is an instance, return the URI of its generic class (if it exists)
    3. If element is a literal appearing in a (subject, property, literal) triple, returns
       the generic element of its subject
    4. Otherwise, just return the element's URI
    :param element: an OntologyElement instance
    :param o: Ontology instance
    :return: string; The URI of the generic element; None if not found
    """
    generic = None
    if isinstance(element, OntologyElement):
        if isinstance(element, OntologyEntityElement):
            generic = getGenericElementofClassURI(element.uri, o)
        elif isinstance(element, (OntologyObjectPropertyElement, OntologyDatatypePropertyElement)):
            generic = getGenericElementofPropertyURI(element.uri, o)
        elif isinstance(element, OntologyInstanceElement):
            classes = element.classUris
            if classes:
                max_spec = -1.0
                top_class = None
                for c in classes:
                    specificity = o.specificityOfElement(c)
                    if specificity > max_spec:
                        top_class = c
                        max_spec = specificity
                generic_classes, _ = o.getTopElements(top_class, 'class')
                generic = generic_classes[0] if generic_classes else element.uri
            else:
                generic = element.uri
        elif isinstance(element, OntologyLiteralElement):
            found = False
            if element.triples:
                first_subject = element.triples[0][0]
                if first_subject:
                    generic = getGenericElementofURI(first_subject, o)
                    found = True
            if not found:
                generic = element.uri  # URI actually contains value of Literal
        else:
            generic = element.uri
    return str(generic)


def getGenericElementofURI(element_uri, o):
    """
    Given the URI of an unknown ontology resource, return its generic element URI
    :param element_uri: An URI in the ontology
    :param o: Ontology instance
    :return: string; The URI of the generic element
    """
    ns = o.getNamespace(element_uri)
    name = o.stripNamespace(element_uri)
    if o.classExists(name, ns):
        generic = getGenericElementofClassURI(element_uri, o)
    elif o.propertyExists(name, 'all', ns):
        generic = getGenericElementofPropertyURI(element_uri, o)
    elif o.individualExists(name, ns):
        generic = getGenericElementofIndividualURI(element_uri, o)
    else:
        generic = element_uri
    return generic


def getGenericElementofClassURI(class_uri, o):
    """
    Given the URI of an class, return its generic element URI
    :param class_uri: An URI in the ontology
    :param o: Ontology instance
    :return: string; The URI of the generic element (top-level parent class)
    """
    generic_classes, _ = o.getTopElements(class_uri, 'class')
    return generic_classes[0] if generic_classes else class_uri


def getGenericElementofPropertyURI(prop_uri, o):
    """
    Given the URI of an property, return its generic element URI
    :param prop_uri: An URI in the ontology
    :param o: Ontology instance
    :return: string; The URI of the generic element (top-level parent property)
    """
    generic_props, _ = o.getTopElements(prop_uri, 'property')
    return generic_props[0] if generic_props else prop_uri


def getGenericElementofIndividualURI(ind_uri, o):
    """
    Given the URI of an individual, return its generic element URI (usually a class)
    :param ind_uri: An URI in the ontology
    :param o: Ontology instance
    :return: string; The URI of the generic element
    """
    class_uris = o.getClassOfElement(ind_uri, stripns=False)
    if class_uris:
        max_spec = -1.0
        top_class = None
        for c in class_uris:
            specificity = o.specificityOfElement(c)
            if specificity > max_spec:
                top_class = c
                max_spec = specificity
        generic = getGenericElementofClassURI(top_class, o)
    else:
        generic = ind_uri
    return generic


def updateVoteScores(suggestion_pair, vote_id):
    """
    Updates the learning scores for a given dialogue
    :param suggestion_pair: SuggestionPair instance shown to the user in a dialogue
    :param vote_id: string; id of the suggestion the user chose
    :return: list<Vote> list of chosen votes; generally only one
    """
    votes = []
    if isinstance(suggestion_pair, SuggestionPair) and vote_id:
        for v in suggestion_pair.votes:
            if v.id:
                if v.id == vote_id:
                    v.vote += CHOSEN_REWARD
                    votes.append(v)
                else:
                    v.vote += NEGATIVE_REWARD
    return votes


def updateLearningModel(suggestion_pair, o):
    """
    Updates the learning model after a user dialogue
    :param suggestion_pair: SuggestionPair instance with newly computed votes from a user selection
    :param o: Ontology instance
    :return: None; learning model is updated
    """
    if isinstance(suggestion_pair, SuggestionPair) and suggestion_pair.key.nearest_neighbors:
        from dialog.model.modelUtil import saveLearningModel
        model = {}
        lvotes = getLearningVotesfromVotes(suggestion_pair.votes)
        if suggestion_pair.key.nearest_neighbors:
            for sc in suggestion_pair.key.nearest_neighbors:
                key = Key(suggestion_pair.key.text)
                key.instance_uris = list(suggestion_pair.key.instance_uris)
                key.triples = list(suggestion_pair.key.triples)
                key.oe_id = getGenericElement(sc.OE, o)
                model[key] = list(lvotes)
        else:
            key = Key(suggestion_pair.key.text)
            key.instance_uris = list(suggestion_pair.key.instance_uris)
            key.triples = list(suggestion_pair.key.triples)
            key.oe_id = Key.NEIGHBORS_NONE
            model[key] = lvotes
        if model:
            saveLearningModel(model)


def getLearningVotesfromVotes(votes):
    """
    Create LearningVote instances from the given votes
    :param votes: list<Vote>
    :return: list<LearningVote>
    """
    lvotes = []
    for vote in votes:
        lvote = LearningVote()
        lvote.id = vote.id
        lvote.score = vote.vote
        if vote.candidate:
            lvote.task = vote.candidate.task
            if vote.candidate.OE:
                lvote.identifier = vote.candidate
        lvotes.append(lvote)
    return lvotes


def updateVotesFromLearningVotes(lvotes, old_votes):
    """
    Update Vote instances from the given learning votes
    :param votes: list<LearningVote>
    :param old_votes: list<Vote>; Vote instances to update
    :return: list<Vote>; list of Votes with updated vote scores
    """
    for lvote in lvotes:
        for old_vote in old_votes:
            if old_vote.candidate and old_vote.candidate.OE:
                if lvote.identifier == old_vote.candidate:
                    if lvote.task is None or lvote.task == old_vote.candidate.task:
                        old_vote.vote = lvote.score
    return old_votes
