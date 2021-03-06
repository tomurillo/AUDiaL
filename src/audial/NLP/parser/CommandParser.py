from ontology.upper_vis_ontology import UpperVisOntology


class CommandParser(object):
    """
    Finds quick commands in a user's query skipping Parse Tree generation and other complex NLP
    """
    def __init__(self, what):
        """
        CommandParser constructor
        :param what: string; normalized user query
        """
        self.what = what
        self.shortcuts = self.__initShortcuts()

    def queryToTask(self):
        """
        Tries to find navigational commands in the user query
        :return: string; the task name if found; None otherwise
        """
        task = self.shortcuts.get(self.what)  # Common shortcuts
        if not task:
            import re
            from regexes import QuickRegex
            rx = QuickRegex()
            # Navigational tasks
            for regex in rx.nav_regexes:
                p = re.compile(regex, re.IGNORECASE)
                m = p.match(self.what)
                if m:
                    task = self.shortcuts.get(m.group(1))
                    if task:
                        return task
            for regex in rx.where_regexes:
                p = re.compile(regex, re.IGNORECASE)
                m = p.match(self.what)
                if m:
                    return UpperVisOntology.StructuralTask.NavigationTask.WHERE
            # Set home task
            p = re.compile(rx.SET_HOME, re.IGNORECASE)
            m = p.match(self.what)
            if m:
                return UpperVisOntology.StructuralTask.NavigationTask.SET_HOME
            for regex in rx.summary_regexes:
                p = re.compile(regex, re.IGNORECASE)
                m = p.match(self.what)
                if m:
                    return UpperVisOntology.StructuralTask.ReadingTask.SUMMARY
        return task

    def __initShortcuts(self):
        """
        Return the task shortcut dictionary
        :return: dict<string; Task>
        """
        shortcuts = {
            'start': UpperVisOntology.StructuralTask.NavigationTask.GOTO_FIRST,
            'go to start': UpperVisOntology.StructuralTask.NavigationTask.GOTO_FIRST,
            'starting': UpperVisOntology.StructuralTask.NavigationTask.GOTO_FIRST,
            'first': UpperVisOntology.StructuralTask.NavigationTask.GOTO_FIRST,
            'go to first': UpperVisOntology.StructuralTask.NavigationTask.GOTO_FIRST,
            'beginning': UpperVisOntology.StructuralTask.NavigationTask.GOTO_FIRST,
            'initial': UpperVisOntology.StructuralTask.NavigationTask.GOTO_FIRST,
            'leftmost': UpperVisOntology.StructuralTask.NavigationTask.GOTO_FIRST,
            'gtf': UpperVisOntology.StructuralTask.NavigationTask.GOTO_FIRST,
            'last': UpperVisOntology.StructuralTask.NavigationTask.GOTO_LAST,
            'go to last': UpperVisOntology.StructuralTask.NavigationTask.GOTO_LAST,
            'rightmost': UpperVisOntology.StructuralTask.NavigationTask.GOTO_LAST,
            'end': UpperVisOntology.StructuralTask.NavigationTask.GOTO_LAST,
            'go to end': UpperVisOntology.StructuralTask.NavigationTask.GOTO_FIRST,
            'ending': UpperVisOntology.StructuralTask.NavigationTask.GOTO_LAST,
            'gtl': UpperVisOntology.StructuralTask.NavigationTask.GOTO_LAST,
            'highest': UpperVisOntology.StructuralTask.NavigationTask.GOTO_HIGHEST,
            'tallest': UpperVisOntology.StructuralTask.NavigationTask.GOTO_HIGHEST,
            'biggest': UpperVisOntology.StructuralTask.NavigationTask.GOTO_HIGHEST,
            'lowest': UpperVisOntology.StructuralTask.NavigationTask.GOTO_LOWEST,
            'shortest': UpperVisOntology.StructuralTask.NavigationTask.GOTO_LOWEST,
            'smallest': UpperVisOntology.StructuralTask.NavigationTask.GOTO_LOWEST,
            'go left': UpperVisOntology.StructuralTask.NavigationTask.MOVE_LEFT,
            'move left': UpperVisOntology.StructuralTask.NavigationTask.MOVE_LEFT,
            'left': UpperVisOntology.StructuralTask.NavigationTask.MOVE_LEFT,
            'previous': UpperVisOntology.StructuralTask.NavigationTask.MOVE_LEFT,
            'prev': UpperVisOntology.StructuralTask.NavigationTask.MOVE_LEFT,
            'right': UpperVisOntology.StructuralTask.NavigationTask.MOVE_RIGHT,
            'go right': UpperVisOntology.StructuralTask.NavigationTask.MOVE_RIGHT,
            'move right': UpperVisOntology.StructuralTask.NavigationTask.MOVE_RIGHT,
            'next': UpperVisOntology.StructuralTask.NavigationTask.MOVE_RIGHT,
            'following': UpperVisOntology.StructuralTask.NavigationTask.MOVE_RIGHT,
            'up': UpperVisOntology.StructuralTask.NavigationTask.MOVE_UP,
            'go up': UpperVisOntology.StructuralTask.NavigationTask.MOVE_UP,
            'move up': UpperVisOntology.StructuralTask.NavigationTask.MOVE_UP,
            'parent': UpperVisOntology.StructuralTask.NavigationTask.MOVE_UP,
            'ancestor': UpperVisOntology.StructuralTask.NavigationTask.MOVE_UP,
            'down': UpperVisOntology.StructuralTask.NavigationTask.MOVE_DOWN,
            'go down': UpperVisOntology.StructuralTask.NavigationTask.MOVE_DOWN,
            'move down': UpperVisOntology.StructuralTask.NavigationTask.MOVE_DOWN,
            'descendant': UpperVisOntology.StructuralTask.NavigationTask.MOVE_DOWN,
            'child': UpperVisOntology.StructuralTask.NavigationTask.MOVE_DOWN,
            'reset': UpperVisOntology.StructuralTask.NavigationTask.RESET,
            'current': UpperVisOntology.StructuralTask.NavigationTask.WHERE,
            'where': UpperVisOntology.StructuralTask.NavigationTask.WHERE,
            'position': UpperVisOntology.StructuralTask.NavigationTask.WHERE,
            'current position': UpperVisOntology.StructuralTask.NavigationTask.WHERE,
            'wai': UpperVisOntology.StructuralTask.NavigationTask.WHERE,
            'home': UpperVisOntology.StructuralTask.NavigationTask.GOTO_HOME,
            'goto home' : UpperVisOntology.StructuralTask.NavigationTask.GOTO_HOME,
            'go to home': UpperVisOntology.StructuralTask.NavigationTask.GOTO_HOME,
            'jump to home': UpperVisOntology.StructuralTask.NavigationTask.GOTO_HOME,
            'move to home': UpperVisOntology.StructuralTask.NavigationTask.GOTO_HOME,
            'favorite': UpperVisOntology.StructuralTask.NavigationTask.GOTO_HOME,
            'favourite': UpperVisOntology.StructuralTask.NavigationTask.GOTO_HOME,
            'main': UpperVisOntology.StructuralTask.NavigationTask.GOTO_HOME,
            'set home': UpperVisOntology.StructuralTask.NavigationTask.SET_HOME,
            'set main': UpperVisOntology.StructuralTask.NavigationTask.SET_HOME,
            'set current home': UpperVisOntology.StructuralTask.NavigationTask.SET_HOME,
            'set current as home': UpperVisOntology.StructuralTask.NavigationTask.SET_HOME,
            'set current as main': UpperVisOntology.StructuralTask.NavigationTask.SET_HOME,
            'set favourite': UpperVisOntology.StructuralTask.NavigationTask.SET_HOME,
            'set favorite': UpperVisOntology.StructuralTask.NavigationTask.SET_HOME,
            'summary': UpperVisOntology.StructuralTask.ReadingTask.SUMMARY,
            'retrieve summary': UpperVisOntology.StructuralTask.ReadingTask.SUMMARY,
            'get summary': UpperVisOntology.StructuralTask.ReadingTask.SUMMARY,
            'overview': UpperVisOntology.StructuralTask.ReadingTask.SUMMARY,
            'retrieve overview': UpperVisOntology.StructuralTask.ReadingTask.SUMMARY,
            'get overview': UpperVisOntology.StructuralTask.ReadingTask.SUMMARY,
            'summarize': UpperVisOntology.StructuralTask.ReadingTask.SUMMARY,
        }
        return shortcuts
