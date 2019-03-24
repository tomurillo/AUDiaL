"""
POC constants
"""

TOKEN_IGNORE_PAIR = ["show me", "give me", "tell me", "show us", "give us", "tell us"]

# Redundant tasks and commands, will be evaluated as filtering tasks if not other task OC found in query
TASK_IGNORE = ["go", "proceed", "move", "show", "give", "tell", "say", "output", "compute", "calculate", "infer", "is",
               "are", "was", "were"]

# Adverbs that can be ignored
RB_IGNORE = ["there"]
