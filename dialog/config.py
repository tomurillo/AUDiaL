"""
Dialogue configuration constants
"""

FORCE_SUGGESTIONS = False  # Whether to force creation of suggestions during dialogue if none have been found

MAX_SUGGESTIONS = 100  # Maximum number of suggestions to display to the user at once in a dialogue

USE_LABELS = True  # Whether to return resource's labels in the dialogue instead of their URIs

MIN_VOTE_DIFF_RESOLVE = 5  # Minimum difference between max. voted suggestion and the rest to automatically cast vote

#  Label property URIs (besides rdfs:label) to be looked for, in order. To be shown in dialog suggestions for each element.
LABEL_PROPS = ['http://purl.org/dc/terms/title', 'http://purl.org/dc/elements/1.1/title']

FORCE_DIALOG = False

"""
Weights of each criteria when computing suggestion votes (must sum up to 1):
1. Main similarity (Monge-Elkan distance) between user input and suggestion
2. Phonetic similarity (soundmax) between user input and suggestion 
3. Similarity with synonyms
"""
VOTE_CRITERIA_WEIGHTS = [0.45, 0.15, 0.4]

"""
List of numerical tasks that will be included in suggestions for Datatype properties
"""
QUICK_TASKS = ['max', 'min', 'sum', 'avg']
