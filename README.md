# GraphNav

(Work in progress)

A Python Web application prototype of a Natural Language Interface (**NLI**) to **RDF**-based semantically-enhanced **diagrams** (i.e. knowledge representation graphics). Built with [Flask](http://flask.pocoo.org/), [NLTK](https://www.nltk.org/), the [Stanford Parser](https://nlp.stanford.edu/software/lex-parser.shtml), and [RDFLib](https://rdflib.readthedocs.io). Code for initial NL Query consolidation taken from [FREyA](http://services.gate.ac.uk/freya/)

## System Requirements

- Python 2.7 (optionally pip)
- Java JDK (1.8+)

## Install (Windows)
1. Set the `JAVA_HOME` environment to `C:\Program Files\Java\jdk1.X.X_XXX` or similar
2. Install Python libraries (on your venv terminal):
    ```
    pip install Flask
    pip install rdflib
    pip install nltk
    ```
3. Download the [basic English Stanford Tagger](https://nlp.stanford.edu/software/tagger.shtml#Download) (tested with version 3.9.1).
4. Unzip the contents of step 3 such that `stanford-postagger-X.X.X.jar` is under `/NLP/lib/postaggers/stanford-postagger`.
5. Download the [Stanford Parser](https://nlp.stanford.edu/software/lex-parser.shtml#Download) (tested with version 3.9.1).
4. Unzip the contents of step 5 such that `stanford-parser-X.X.X-models.jar` is under `/NLP/lib/parsers/stanford-parser-full`.
7. Add the Wordnet corpus to NLTK:
    ```
    python
    > import nltk
    > nltk.download('wordnet')
    ```

## Usage
- Run locally:
  - `python path/to/project/__init__.py`
  - Visit `127.0.0.1:54634`
  
- Debug with PyDev:
  - `python "path\to\pydev\pydevd.py" --multiproc --qt-support=auto --client 127.0.0.1 --port 54634 --file path/to/project/__init__.py`