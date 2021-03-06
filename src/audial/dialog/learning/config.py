"""
Suggestion learning configuration constants
"""

LEARNING_ENABLED = True

# Reward given to resources chosen by the user in a dialogue
CHOSEN_REWARD = 1.0

# Reward given to resources not chosen by the user in a dialogue
NEGATIVE_REWARD = -0.1

# Whether to give priority to textual labels of the diagram in dialogues
PRIORITY_DIAG_LABELS = True
