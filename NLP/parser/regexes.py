"""
Regular Expressions for quick task finding
"""


class QuickRegex(object):
    def __init__(self):
        # Move to previous/next/etc.
        self.HOME = 'home|favou?rite|main'
        self.DIRECTION = 'next|right|rightmost|previous|left|leftmost|following|first|last|highest|tallest|biggest|'
        self.DIRECTION += 'current|shortest|smallest|start|starting|end|ending|beginning|initial|parent|ancestor|child|'
        self.DIRECTION += 'descendant|up|down|'
        self.DIRECTION += self.HOME
        self.DIR_VERB = 'move|go|proceed|advance|progress|get to|bring me|jump'
        self.MOVE_REGEX_SHORT = '\s*(%s)\s+\w+\W*' % self.DIRECTION
        self.MOVE_REGEX_LONG = \
            '.*(?:%s)(?:\s+to(?:wards)?\s)?(?:\s+the\s)?(?:\s+\w+)*\s+(%s)(?:\s+\w+)*(?:\W*)?$' % \
            (self.DIR_VERB, self.DIRECTION)

        self.nav_regexes = [self.MOVE_REGEX_SHORT, self.MOVE_REGEX_LONG]
        # Set home node
        self.SET_VERB = 'set|assign|fix|apply|establish|put'
        self.NODE = 'node|bar|element|object|point|place|thing'
        self.SET_HOME = '\s*?(?:%s)\s+.*?(%s)\s+(?:%s).*' % (self.SET_VERB, self.HOME, self.NODE)
        # Print summary
        self.SUMMARY_VERB_1 = 'print|give|output|generate|fetch|issue|read|deliver'
        self.SUMMARY_OBJ_1 = 'summary|outline|recap|synopsis|rundown|sketch|abridgment|report|abbreviation|overview'
        self.SUMMARY_VERB_2 = 'summarize|outline|sum up|recap|abridge|digest|shorten|skim|review|condense'
        self.SUMMARY_OBJ_2 = 'image|graphic|chart|diagram|figure|drawing|illustration|model|it|this|outline'
        self.SUMMARY_1 = '^(?:.*\s)?(?:%s)(?:(?:\s.*?\s)|\s*)?(%s)(?:\W.*)?$' % \
                         (self.SUMMARY_VERB_1, self.SUMMARY_OBJ_1)
        self.SUMMARY_2 = '^(?:.*\s)?(%s)(?:(?:\s.*?\s)|\s*)?(?:%s)(?:\W.*)?$' % \
                         (self.SUMMARY_VERB_2, self.SUMMARY_OBJ_2)
        self.summary_regexes = [self.SUMMARY_1, self.SUMMARY_2]
        # Where am I?
        self.WAI_1 = '^(?:.*\s)?where(?:(?:\s.*?\s)|\s*)?((am i)|(i am)).*$'
        self.WAI_2 = '^(?:.*\s)?where(?:(?:\s.*?\s)|\s*)?(are we|we are|you are|are you).*$'
        self.WAI_3 = '^(?:.*\s)?(my|our|your)(?:(?:\s.*?\s)|\s*)?(location|position|whereabouts).*$'
        self.where_regexes = [self.WAI_1, self.WAI_2, self.WAI_3]
