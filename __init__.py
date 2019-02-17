import os
import traceback

from flask import Flask, render_template, jsonify, request

from Ontovis.bar_chart_ontology import *
from content_management import Content
from controller import *

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True
# Bubble HTTP exceptions through the exception stack
app.config['TRAP_HTTP_EXCEPTIONS'] = True

GRAPHICS = Content()

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

def loadPersistentOntology(RDFpath=None, current=None):
    """Tries to fetch a persitent ontology. If it does not find it, it loads a
    new one from the RDF file whose path is passed"""
    if current == 'Bar Chart':
        o = BarChartOntology(RDFpath)
    else:
        o = UpperOntology(RDFpath)
    return o

@app.route('/')
@app.route('/bar-chart-austria')
def homepage():
    try:
        current = "Bar Chart"
        c = Controller(current, ontologyPath(GRAPHICS[current][4]))
        curBarTags = ""
        if c.isOntologyLoaded():
            curBarTags = c.o.getCurrentBarUserTags()
        c.clean()
        return render_template("graphic_nav.html",
                               GRAPHICS=GRAPHICS,
                               current=current,
                               curBarTags=curBarTags,
                               output='Please enter a query below',
                               output_type='result')
    except Exception as e:
        return printException(e)

@app.route('/_retrieve_values')
def retrieve_values():
    try:
        current = request.args.get('current_graphic', '')
        to_count = request.args.get('to_count', '')
        to_retrieve = request.args.get('to_retrieve', '')
        output_type = 'answer'
        c = Controller(current)
        if c.isOntologyLoaded():
            output = "No results"
            if to_count:
                output = c.retrieveCount(to_count)
            elif to_retrieve:
                output, output_type = c.retrieveValue(to_retrieve)
        else:
            output = "Ontology not loaded!"
        curBarTags = ""
        if c.isOntologyLoaded():
            curBarTags = c.o.getCurrentBarUserTags()
        c.clean()
        return render_template("graphic_nav.html",
                               GRAPHICS=GRAPHICS,
                               current=current,
                               curBarTags=curBarTags,
                               output=output,
                               output_type=output_type)
    except Exception as e:
        return jsonify(result=printException(e))

@app.route('/_filter')
def query_filter():
    try:
        current = request.args.get('current_graphic', '')
        filter = request.args.get('to_filter', '')
        c = Controller(current)
        if c.isOntologyLoaded():
            output = "No results"
            if filter:
                output, _ = c.retrieveNumeric(filter)
            else:
                output = "No filter input"
        else:
            output = "Ontology not loaded!"
        c.clean()
        return jsonify(result=output)
    except Exception as e:
        return jsonify(result=printException(e))

@app.route('/_derived_value')
def query_derived_value():
    try:
        current = request.args.get('current_graphic', '')
        query = request.args.get('query', '')
        queryExtreme = request.args.get('queryExtreme', '')
        querySort =  request.args.get('querySort', '')
        queryRange = request.args.get('queryRange', '')
        c = Controller(current)
        if c.isOntologyLoaded():
            output = ""
            if query:
                output, _ = c.retrieveDerivedValue(query)
            elif queryExtreme:
                output, _ = c.retrieveExtreme(queryExtreme)
            elif querySort:
                output = c.retrieveSorted(querySort)
            elif queryRange:
                output , _ = c.retrieveRange(queryRange)
            else:
                output = "No input"
        else:
            output = "Ontology not loaded!"
        c.clean()
        return jsonify(result=output)
    except Exception as e:
        return jsonify(result=printException(e))

@app.route('/_overview')
def overview():
    try:
        current = request.args.get('current_graphic', '')
        c = Controller(current)
        output = c.retrieveSummary()
        c.clean()
        return jsonify(result=output)
    except Exception as e:
        return jsonify(result=printException(e))

@app.route('/_navigate')
def navigate():
    try:
        current = request.args.get('current_graphic', '')
        action = request.args.get('action', '')
        c = Controller(current)
        output = c.navigate(action)
        usertags = c.o.getCurrentBarUserTags()
        c.clean()
        return jsonify(result=output,
                       usertags=usertags)
    except Exception as e:
        return jsonify(result=printException(e),
                       usertags="")

@app.route('/_add_user_tags')
def addUserTagsToCurrentBar():
    try:
        current = request.args.get('current_graphic', '')
        usertags = request.args.get('user_tags', '')
        c = Controller(current)
        output = c.setUserTags(usertags, to='current')
        c.clean()
        return jsonify(result=output,
                       usertags=usertags)
    except Exception as e:
        return jsonify(result=printException(e),
                       usertags="")

@app.route('/_fetch_intention')
def fetchIntention():
    try:
        current = request.args.get('current_graphic', '')
        force = request.args.get('force_exec', '')
        c = Controller(current)
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
        return jsonify(result=printException(e))

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

def printException(e):
    """
    Pretty-print an exception
    @param e: The exception object
    @return string: the information to be printed
    """
    t = traceback.format_exc()
    pretty_e =  "%s\n%s" % (str(e), t)
    return pretty_e.replace("\n", "<br/>")

if __name__ == '__main__':
    app.run()
