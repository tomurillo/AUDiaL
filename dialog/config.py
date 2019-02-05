"""
Dialogue configuration constants
"""

FORCE_SUGGESTIONS = False  # Whether to force creation of suggestions during dialogue if none have been found

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
