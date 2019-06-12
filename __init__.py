import traceback
from flask import Flask, render_template, jsonify, request
from flask_session import Session
from content_management import Content
from controller import Controller
from flask import session
import os
from config import *


#  Bootstrapping
root_dir = os.path.dirname(__file__)
app = Flask(__name__)
SESSION_TYPE = 'filesystem'
SESSION_FILE_DIR = os.path.join(root_dir, 'flask_session')
app.config.from_object(__name__)
Session(app)
app.config['DEBUG'] = FLASK_DEBUG
app.config['PROPAGATE_EXCEPTIONS'] = FLASK_BUBBLE_EXCEPTIONS
app.config['TRAP_HTTP_EXCEPTIONS'] = FLASK_BUBBLE_EXCEPTIONS
app.secret_key = FLASK_SECRET_KEY

GRAPHICS = Content()


@app.route('/')
@app.route('/bar-chart-austria')
def homepage():
    c = None
    try:
        key = "Austrian Population"
        current = GRAPHICS[key][5]
        c = Controller(current, ontologyPath(GRAPHICS[key][4]), GRAPHICS[key][6])
        curBarTags = ""
        if c.isOntologyLoaded():
            curBarTags = c.o.getCurrentBarUserTags()
        c.clearSessionContext()
        c.clean()
        return render_template("graphic_nav.html",
                               GRAPHICS=GRAPHICS,
                               current=key,
                               curBarTags=curBarTags,
                               output='Please enter a query below',
                               output_type='result')
    except Exception as e:
        if c:
            c.clearSessionContext()
            c.clean()
        else:
            session.clear()
        return printException(e)


@app.route('/bar-chart-leo-dicaprio')
def bar_chart_caprio():
    c = None
    try:
        key = "Leonardo DiCaprio"
        c = Controller(GRAPHICS[key][5], ontologyPath(GRAPHICS[key][4]), GRAPHICS[key][6])
        curBarTags = ""
        if c.isOntologyLoaded():
            curBarTags = c.o.getCurrentBarUserTags()
        c.clearSessionContext()
        c.clean()
        return render_template("graphic_nav.html",
                               GRAPHICS=GRAPHICS,
                               current=key,
                               curBarTags=curBarTags,
                               output='Please enter a query below',
                               output_type='result')
    except Exception as e:
        if c:
            c.clearSessionContext()
            c.clean()
        else:
            session.clear()
        return printException(e)


@app.route('/_retrieve_values')
def retrieve_values():
    c = None
    try:
        current = request.args.get('current_graphic', '')
        to_retrieve = request.args.get('to_retrieve', '')
        output_type = 'answer'
        c = Controller(GRAPHICS[current][5], sess_id=GRAPHICS[current][6])
        c.clearSessionContext()
        if c.isOntologyLoaded():
            output = ''
            if to_retrieve:
                output, output_type = c.retrieveValue(to_retrieve)
            if not output:
                output = "No results"
        else:
            output = "Ontology not loaded!"
        if output_type == 'dialogue':
            c.saveContextToSession()
        c.clean()
        return jsonify(result=output,
                       output_type=output_type)
    except Exception as e:
        handleException(e, c)
        return jsonify(result=printException(e), output_type='answer')


@app.route('/_vote_selected')
def vote_selected():
    output_type = 'answer'
    c = None
    try:
        current = request.args.get('current_graphic', '')
        vote_id = request.args.get('vote_id', '')
        c = Controller(GRAPHICS[current][5], sess_id=GRAPHICS[current][6])
        if c.isOntologyLoaded():
            if vote_id:
                output, output_type = c.processVoteSelection(vote_id)
            else:
                output = "Invalid selection! Please try a different one."
        else:
            output = "Ontology not loaded!"
        if output_type == 'dialogue':
            c.saveContextToSession()
        c.clean()
        return jsonify(result=output,
                       output_type=output_type)
    except Exception as e:
        handleException(e, c)
        return jsonify(result=printException(e), output_type='answer')


@app.route('/_overview')
def overview():
    c = None
    try:
        current = request.args.get('current_graphic', '')
        c = Controller(GRAPHICS[current][5], sess_id=GRAPHICS[current][6])
        c.clearSessionContext()
        output = c.retrieveSummary()
        c.clean()
        return jsonify(result=output)
    except Exception as e:
        handleException(e, c)
        return jsonify(result=printException(e), output_type='answer')


@app.route('/_navigate')
def navigate():
    c = None
    try:
        current = request.args.get('current_graphic', '')
        action = request.args.get('action', '')
        c = Controller(GRAPHICS[current][5], sess_id=GRAPHICS[current][6])
        c.clearSessionContext()
        output = c.navigate(action)
        usertags = c.o.getCurrentBarUserTags()
        c.clean()
        return jsonify(result=output,
                       usertags=usertags)
    except Exception as e:
        handleException(e, c)
        return jsonify(result=printException(e), output_type='answer')


@app.route('/_add_user_tags')
def addUserTagsToCurrentBar():
    c = None
    try:
        current = request.args.get('current_graphic', '')
        usertags = request.args.get('user_tags', '')
        c = Controller(GRAPHICS[current][5], sess_id=GRAPHICS[current][6])
        c.clearSessionContext()
        output = c.setUserTags(usertags, to='current')
        c.clean()
        return jsonify(result=output,
                       usertags=usertags)
    except Exception as e:
        handleException(e, c)
        return jsonify(result=printException(e), output_type='answer')


@app.route('/_fetch_intention')
def fetchIntention():
    c = None
    try:
        current = request.args.get('current_graphic', '')
        force = request.args.get('force_exec', '')
        c = Controller(GRAPHICS[current][5], sess_id=GRAPHICS[current][6])
        c.clearSessionContext()
        intentions = c.getAuthorIntentions(force == 'yes')
        html = intentionDictToHTML(intentions)
        if intentions:
            output = "Author's intention fetched. See the intention area for more information."
        else:
             output = "No intentions found."
             if force:
                 output += " Try recomputing the author's intention."
        c.clean()
        return jsonify(result=output,
                       intentions=html)
    except Exception as e:
        handleException(e, c)
        return jsonify(result=printException(e), output_type='answer')


def intentionDictToHTML(intentions):
    """
    Converts an intention dictionary to HTML ready to be embedded.
    @param intentions: an intention dictionary as returned by the controller
    @return string: an HTML list
    """
    html = '<div class="panel-body">'
    if intentions:
        for k in intentions:
            i = intentions[k]
            html += "<p>%s</p>" % i['summary']
            html += '<ul class="list-group">'
            ops = i['operations']
            for k2 in ops:
                o = ops[k2]
                html += '<li class="list-group-item">'
                html += '<ul>'
                html += '<li>Query: %s</li>' % o['query']
                html += '<li>Result: <i>%s</i></li>' % o['spokenresult']
                html += '</ul></li>'
            html += '</ul>'
    else:
        html += "<p>No intention found.</p>"
    html += '</div>'
    return html


def handleException(e, c=None):
    """
    Handle's the user session and persistent objects when an exception happens
    :param e: Exception instance
    :param e: Controller instance
    :return: None
    """
    if c:
        c.clearSessionContext()
        c.clean()
    else:
        session.clear()

def printException(e):
    """
    Pretty-print an exception
    @param e: The exception object
    @return string: the information to be printed
    """
    t = traceback.format_exc()
    pretty_e = "%s\n%s" % (str(e), t)
    return pretty_e.replace("\n", "<br/>")


def ontologyPath(fileName):
    """
    Returns the absolute path to the given serialized ontology file
    :param fileName: string; filename of the serialized ontology
    :return: string; absolute path to the given file, if it exists.
    """
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "static", "graphics", fileName))


if __name__ == '__main__':
    app.run(threaded=True)
