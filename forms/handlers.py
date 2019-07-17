from util import getStoragePath


def process_quest_tasks(form, username, diagram):
    """
    Handles the submission of a tasks evaluation form
    :param form: dict with form values
    :param username: string; name of the user that has submitted the form
    :param diagram: string; name of the diagram being evaluated
    :return: None; form data is serialized to file
    """
    if form and username and diagram:
        store_path = getStoragePath("%s.txt" % diagram, username)
        i = 1
        lines = ["Tasks evaluation (%s) for user %s" % (diagram, username), "\n\n"]
        while True:
            input_name = "answer-task-%d" % i
            difficulty_name = "difficulty-task-%d" % i
            fail_reason_name = "fail-reason-task-%d" % i
            fail_feedback_name = "feedback-task-%d" % i
            if input_name in form:
                input_val = form.get(input_name)
                if not input_val:
                    input_val = 'left empty.'
                lines.append("Task no. %d.\n\nAnswer: %s\n" % (i, input_val))
                if difficulty_name in form:
                    difficulty_val = form.get(difficulty_name)
                    lines.append("Difficulty for task %d: %s\n" % (i, difficulty_val))
                    if difficulty_val == "No, I failed to complete the task":
                        reason_val = form.get(fail_reason_name)
                        lines.append("Reason for failure: %s\n" % reason_val)
                        if reason_val == "Other reason":
                            fail_feedback = form.get(fail_feedback_name)
                            lines.append("Failure feedback: %s\n" % fail_feedback)
                lines.append("\n\n")
                i += 1
            else:
                break
        with open(store_path, 'a') as f:
            f.writelines(lines)


def process_quest_dem(form, username):
    """
    Handles the submission of the demographics form
    :param form: dict with form values
    :param username: string; name of the user that has submitted the form
    :return: None; form data is serialized to file
    """
    if form and username:
        store_path = getStoragePath("demographic.txt", username)
        br_habits_str = 'Browsing Habits:'
        br_habits = []
        diagrams_str = 'Known Diagrams:'
        diagrams = []
        diagram_loc_str = 'Diagrams found in:'
        diagram_loc = []
        sorted_answers = {}
        for k, v in form.iteritems():
            if k == 'age':
                sorted_answers[1] = "Age: %s" % v
            elif k == 'sex':
                sorted_answers[2] = 'Gender: %s' % v
            elif k == 'experience-web':
                sorted_answers[3] = 'Web Browsing Experience: %s' % v
            elif k == 'tech-tts':
                br_habits.append('Text-to-speech')
            elif k == 'tech-bd':
                br_habits.append('Braille Display')
            elif k == 'tech-mag':
                br_habits.append('Screen Magnifier')
            elif k == 'tech-other':
                br_habits.append('Other Assistive Technologies')
            elif k == 'tech-no':
                br_habits.append('None')
            elif k == 'screen-reader':
                sorted_answers[5] = 'Screen Reader: %s' % (v if v else 'none')
            elif k == 'diag-type-bar':
                diagrams.append('Bar Chart')
            elif k == 'diag-type-hist':
                diagrams.append('Histogram')
            elif k == 'diag-type-pie':
                diagrams.append('Pie Chart')
            elif k == 'diag-type-line':
                diagrams.append('Line Chart')
            elif k == 'diag-type-scatter':
                diagrams.append('Scatter Plot')
            elif k == 'diag-type-area':
                diagrams.append('Area Chart')
            elif k == 'diag-type-graph':
                diagrams.append('Link Diagram')
            elif k == 'diag-type-euler':
                diagrams.append('Group Diagram')
            elif k == 'diag-type-other' and v:
                diagrams.append(v)
            elif k == 'diag-freq':
                sorted_answers[7] = 'Diagrams encountered: %s' % v
            elif k == 'diag-news':
                diagram_loc.append('News Sites')
            elif k == 'diag-uni':
                diagram_loc.append('University Sites')
            elif k == 'diag-game':
                diagram_loc.append('Online Games')
            elif k == 'diag-sn':
                diagram_loc.append('Social Networks')
            elif k == 'diag-per':
                diagram_loc.append('Personal Sites')
            elif k == 'diag-other':
                diagram_loc.append('Other Sites')
            elif k == 'diag-alttext':
                sorted_answers[9] = 'Alt-text in diagrams found: %s' % v
            elif k == 'diag-longdesc':
                sorted_answers[10] = 'Longdesc in diagrams found: %s' % v
            elif k == 'diag-tactile':
                sorted_answers[11] = 'Tactile Diagrams used: %s' % v
            elif k == 'diag-prefer':
                sorted_answers[12] = 'Preferred manner of accessing diagrams: %s' % v
        sorted_answers[4] = "%s %s" % (br_habits_str, ", ".join(br_habits))
        sorted_answers[6] = "%s %s" % (diagrams_str, ", ".join(diagrams))
        sorted_answers[8] = "%s %s" % (diagram_loc_str, ", ".join(diagram_loc))
        with open(store_path, 'a') as f:
            lines = ["Demographic data for user %s" % username, "\n\n"]
            f.writelines(lines)
            for k in sorted(sorted_answers):
                f.write("%s\n" % sorted_answers[k])
