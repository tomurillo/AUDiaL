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
            'starting': UpperVisOntology.StructuralTask.NavigationTask.GOTO_FIRST,
            'first': UpperVisOntology.StructuralTask.NavigationTask.GOTO_FIRST,
            'beginning': UpperVisOntology.StructuralTask.NavigationTask.GOTO_FIRST,
            'initial': UpperVisOntology.StructuralTask.NavigationTask.GOTO_FIRST,
            'leftmost': UpperVisOntology.StructuralTask.NavigationTask.GOTO_FIRST,
            'gtf': UpperVisOntology.StructuralTask.NavigationTask.GOTO_FIRST,
            'last': UpperVisOntology.StructuralTask.NavigationTask.GOTO_LAST,
            'rightmost': UpperVisOntology.StructuralTask.NavigationTask.GOTO_LAST,
            'end': UpperVisOntology.StructuralTask.NavigationTask.GOTO_LAST,
            'ending': UpperVisOntology.StructuralTask.NavigationTask.GOTO_LAST,
            'gtl': UpperVisOntology.StructuralTask.NavigationTask.GOTO_LAST,
            'highest': UpperVisOntology.StructuralTask.NavigationTask.GOTO_HIGHEST,
            'tallest': UpperVisOntology.StructuralTask.NavigationTask.GOTO_HIGHEST,
            'biggest': UpperVisOntology.StructuralTask.NavigationTask.GOTO_HIGHEST,
            'lowest': UpperVisOntology.StructuralTask.NavigationTask.GOTO_LOWEST,
            'shortest': UpperVisOntology.StructuralTask.NavigationTask.GOTO_LOWEST,
            'smallest': UpperVisOntology.StructuralTask.NavigationTask.GOTO_LOWEST,
            'left': UpperVisOntology.StructuralTask.NavigationTask.MOVE_LEFT,
            'previous': UpperVisOntology.StructuralTask.NavigationTask.MOVE_LEFT,
            'prev': UpperVisOntology.StructuralTask.NavigationTask.MOVE_LEFT,
            'right': UpperVisOntology.StructuralTask.NavigationTask.MOVE_RIGHT,
            'next': UpperVisOntology.StructuralTask.NavigationTask.MOVE_RIGHT,
            'following': UpperVisOntology.StructuralTask.NavigationTask.MOVE_RIGHT,
            'up': UpperVisOntology.StructuralTask.NavigationTask.MOVE_UP,
            'parent': UpperVisOntology.StructuralTask.NavigationTask.MOVE_UP,
            'ancestor': UpperVisOntology.StructuralTask.NavigationTask.MOVE_UP,
            'down': UpperVisOntology.StructuralTask.NavigationTask.MOVE_DOWN,
            'descendant': UpperVisOntology.StructuralTask.NavigationTask.MOVE_DOWN,
            'child': UpperVisOntology.StructuralTask.NavigationTask.MOVE_DOWN,
            'reset': UpperVisOntology.StructuralTask.NavigationTask.RESET,
            'current': UpperVisOntology.StructuralTask.NavigationTask.WHERE,
            'where': UpperVisOntology.StructuralTask.NavigationTask.WHERE,
            'position': UpperVisOntology.StructuralTask.NavigationTask.WHERE,
            'wai': UpperVisOntology.StructuralTask.NavigationTask.WHERE,
            'home': UpperVisOntology.StructuralTask.NavigationTask.GOTO_HOME,
            'favorite': UpperVisOntology.StructuralTask.NavigationTask.GOTO_HOME,
            'favourite': UpperVisOntology.StructuralTask.NavigationTask.GOTO_HOME,
            'main': UpperVisOntology.StructuralTask.NavigationTask.GOTO_HOME,
            'set home': UpperVisOntology.StructuralTask.NavigationTask.SET_HOME,
            'set main': UpperVisOntology.StructuralTask.NavigationTask.SET_HOME,
            'set favourite': UpperVisOntology.StructuralTask.NavigationTask.SET_HOME,
            'set favorite': UpperVisOntology.StructuralTask.NavigationTask.SET_HOME,
            'summary': UpperVisOntology.StructuralTask.ReadingTask.SUMMARY,
            'overview': UpperVisOntology.StructuralTask.ReadingTask.SUMMARY,
            'summarize': UpperVisOntology.StructuralTask.ReadingTask.SUMMARY,
        }
        return shortcuts
