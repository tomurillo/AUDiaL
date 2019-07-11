import traceback
from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_session import Session
from functools import wraps
from auth_secrets import *
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
DEFAULT_KEY = "Austrian Population"


@app.route('/')
def homepage():
    key = DEFAULT_KEY
    if request.args.get('longdesc') is None:
        return render_graphic(key)
    else:
        return render_longdesc(key)


@app.route('/bar-chart-austria')
def bar_chart_austria():
    key = "Austrian Population"
    if request.args.get('longdesc') is None:
        return render_graphic(key)
    else:
        return render_longdesc(key)


@app.route('/bar-chart-leo-dicaprio')
def bar_chart_caprio():
    key = "Leonardo DiCaprio"
    if request.args.get('longdesc') is None:
        return render_graphic(key)
    else:
        return render_longdesc(key)


@app.route('/bar-chart-power')
def bar_chart_power():
    key = "Power in Europe"
    if request.args.get('longdesc') is None:
        return render_graphic(key)
    else:
        return render_longdesc(key)


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


# Administrative handles
def validate_admin_action(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = session.get('logged_in', False) and session.get('username', '') in ADMINS
        if auth:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login_form'))
    return wrapper


@app.route('/audial-login')
def login_form():
    return render_template("login.html", GRAPHICS=GRAPHICS, current=DEFAULT_KEY)

@app.route('/audial-logout')
def logout():
    if 'username' and 'logged_in' in session:
        session.pop('username')
        session.pop('logged_in')
    return redirect(url_for('homepage'))


@app.route('/handle-login', methods=['POST'])
def login_handle():
    name, pwd = request.form['username'], request.form['pwd']
    if name in ADMINS and pwd == ADMINS[name]:
        session['username'] = name
        session['logged_in'] = True
        return redirect(url_for('homepage'))
    else:
        return redirect(url_for('login_form'))


@app.route('/admin-delete/<command>')
@validate_admin_action
def admin_delete(command):
    from general_util import deleteDirContents
    error_msg = ''
    succ = True
    if command in ['ontology', 'o', 'all']:
        paths = serializedOntologyDirs()
        if paths:
            import shutil
            for p in paths:
                try:
                    shutil.rmtree(p)
                except Exception as e:
                    succ = False
                    error_msg = str(e)
                    break
    if command in ['logs', 'l', 'all']:
        import logging
        path = os.path.normpath(os.path.join(os.path.dirname(__file__), "logger", "logs"))
        try:
            logging.shutdown()
            deleteDirContents(path, ignore=[".keep", "GraphNav.logger.Logger.log"])
        except Exception as e:
            succ = False
            error_msg = str(e)
    if command in ['votes', 'v', 'all']:
        path = os.path.normpath(os.path.join(os.path.dirname(__file__), "dialog", "storage", "votes.json"))
        try:
            with open(path, "w") as f:
                f.write("{}")  # Empty learning model
        except Exception as e:
            succ = False
            error_msg = str(e)
    if command in ['session', 's', 'all']:
        path = os.path.normpath(os.path.join(os.path.dirname(__file__), "flask_session"))
        try:
            session.clear()
            deleteDirContents(path)
        except Exception as e:
            succ = False
            error_msg = str(e)
    if succ:
        return redirect(url_for('homepage'))
    else:
        error_full = "An error occurred: %s" % error_msg
        return jsonify(result=error_full, output_type='answer')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', GRAPHICS=GRAPHICS, current=DEFAULT_KEY), 404


def render_graphic(key):
    c = None
    try:
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
        handleException(e, c)
        return jsonify(result=printException(e), output_type='answer')


def render_longdesc(key):
    html = longdescContents(GRAPHICS[key][4])
    return render_template("longdesc.html",
                           GRAPHICS=GRAPHICS,
                           current=key,
                           longdesc_html=html)


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


def ontologyPath(filaname):
    """
    Returns the absolute path to the given serialized ontology file; None to return storage directory
    :param filaname: string; filename of the serialized ontology
    :return: string; absolute path to the given file, if it exists.
    """
    path = ''
    if filaname:
        path = os.path.normpath(os.path.join(os.path.dirname(__file__), "static", "graphics", filaname))
    return path


def longdescContents(ontology_filename):
    """
    Returns the contents of an HTML file with the long description for the given ontology
    :param ontology_filename: string; filename of a serialized ontology
    :return: string; HTML markup of the longdesc file
    """
    html = ''
    path = ''
    html_file = "%s.html" % os.path.splitext(ontology_filename)[0] if ontology_filename else ''
    if html_file:
        fpath = os.path.normpath(os.path.join(os.path.dirname(__file__), "static", "graphics", "longdesc", html_file))
        if os.path.isfile(fpath):
            path = fpath
    if path:
        with open(path, 'r') as f:
            html = f.read()
    if not html:
        html = 'No long description available.'
    return html


def serializedOntologyDirs():
    """
    Returns all paths to the serialized ontologies in the system
    :return: list<string>: absolute paths to the serialized ontologies
    """
    paths = []
    for _, data in GRAPHICS.iteritems():
        dir_name = "%s_storage" % data[6]
        p = os.path.normpath(os.path.join(os.path.dirname(__file__), "ontology", dir_name))
        if os.path.isdir(p):
            paths.append(p)
    return paths


if __name__ == '__main__':
    app.run(threaded=True)
