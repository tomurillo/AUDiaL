# AUDiaL

**A**ccessible **U**niversal **Dia**grams through **L**anguage
 
A Web-based Natural Language Interface (NLI) to semantically-enhanced diagrams in RDF. Built with [Flask](http://flask.pocoo.org/), [NLTK](https://www.nltk.org/), the [Stanford Parser](https://nlp.stanford.edu/software/lex-parser.shtml), and [RDFLib](https://rdflib.readthedocs.io). Code for initial NLP and dialogue handling derived from [FREyA](https://sites.google.com/site/naturallanguageinterfaces/freya).

(Work in progress)

## System Requirements

- Python 2.7 (optionally pip)
- Java JDK (1.8+)

## Install (Windows)

1. Install the required Python modules (on your venv terminal):
    ```
    pip install Flask
    pip install Flask-Session
    pip install rdflib
    pip install nltk
    pip install requests
    pip install textdistance
    pip install inflect
    ```
2. Optionally, you may also install the following modules for data analysis tasks:
    ```
    pip install scipy
    pip install scikit-learn
    ```
3. Set the `JAVA_HOME` environment to `C:\Program Files\Java\jdk1.X.X_XXX` or similar
4. Download the [basic English Stanford Tagger](https://nlp.stanford.edu/software/tagger.shtml#Download) (tested with version 3.9.1).
5. Unzip the contents of step 3 such that `stanford-postagger-X.X.X.jar` is under `/NLP/lib/postaggers/stanford-postagger`.
6. Download the [Stanford Parser](https://nlp.stanford.edu/software/lex-parser.shtml#Download) (tested with version 3.9.1).
7. Unzip the contents of step 5 such that `stanford-parser-X.X.X-models.jar` is under `/NLP/lib/parsers/stanford-parser-full`.
8. Add the Wordnet corpus to NLTK:
    ```
    python
    > import nltk
    > nltk.download('wordnet')
    ```
    
Steps 3-7 are only required if you want to run the Stanford Parser and POS-tagger locally. It is recommended to use the [Stanford CoreNLP](https://stanfordnlp.github.io/CoreNLP/) API instead. AUDiaL can be configured to use either option:

- **Local NLP**: set the `NLP_PARSER` and `NLP_POS_TAGGER` constants of the main configuration file (`/config.py`) to `'stanford'`.
- **CoreNLP API**: set the `NLP_PARSER` and `NLP_POS_TAGGER` constants of the main configuration file (`/config.py`) to `'stanford_web'`. In the NLP parser config file (`/NLP/parser/config.py`) set the corresponding values for each configuration constant. An example file can be found under `/NLP/parser/config-default.py`

## Usage
- Run locally:
  - `python path/to/project/__init__.py`
  - Visit `127.0.0.1:54634`
  
- Debug with PyDev:
  - `python "path\to\pydev\pydevd.py" --multiproc --qt-support=auto --client 127.0.0.1 --port 54634 --file path/to/project/__init__.py`