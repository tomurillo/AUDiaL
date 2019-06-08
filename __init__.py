import traceback
from flask import Flask, render_template, jsonify, request
from flask_session import Session
from content_management import Content
from controller import Controller
from flask import session
import const as c
import os

from config import *

app = Flask(__name__)
SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)
app.config['DEBUG'] = FLASK_DEBUG
app.config['PROPAGATE_EXCEPTIONS'] = FLASK_BUBBLE_EXCEPTIONS
# Bubble HTTP exceptions through the exception stack
app.config['TRAP_HTTP_EXCEPTIONS'] = FLASK_BUBBLE_EXCEPTIONS
app.secret_key = FLASK_SECRET_KEY

GRAPHICS = Content()


@app.route('/')
@app.route('/bar-chart-austria')
def homepage():
    c = None
    try:
        current = "Bar Chart"
        c = Controller(current, ontologyPath(GRAPHICS[current][4]))
        curBarTags = ""
        if c.isOntologyLoaded():
            curBarTags = c.o.getCurrentBarUserTags()
        c.clearSessionContext()
        c.clean()
        return render_template("graphic_nav.html",
                               GRAPHICS=GRAPHICS,
                               current=current,
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
        to_count = request.args.get('to_count', '')
        to_retrieve = request.args.get('to_retrieve', '')
        output_type = 'answer'
        c = Controller(current)
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
        c = Controller(current)
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
        c = Controller(current)
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
        c = Controller(current)
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
        c = Controller(current)
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
        c = Controller(current)
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
    if c.CURR_ENV == 'windows':
        path = os.path.realpath(__file__)
        if path.endswith("pyc"):
            path = path[:-len("__init__.pyc")]
        else:
            path = path[:-len("__init__.py")]
        return path + "static\\graphics\\%s" % fileName
    else:
        return "/home/FlaskApp/FlaskApp/static/graphics/%s" % fileName


if __name__ == '__main__':
    app.run(threaded=True)
