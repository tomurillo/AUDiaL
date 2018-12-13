import json
import os
from GeneralUtil import asWindows

MODEL_FILE = '../storage/votes.json'


def loadLearningModel():
    """
    Load the current learning model from a serialized file on disk
    :return:
    """
    model_path = getLearningModelPath()
    model = {}
    try:
        with open(model_path, 'a+') as f:
            model = json.load(f)
    except Exception:
        import sys
        print('Learning model could not be loaded from path: %s' % model_path, sys.stderr)
    return model


def saveLearningModel(model):
    """
    Serialize and store a learning model to disk
    :param model: A dict containing the learning model
    :return: True on successful storage; False otherwise
    """
    model_path = getLearningModelPath()
    success = True
    try:
        with open(model_path, 'w') as f:
            json.dump(model, f)
    except Exception:
        import sys
        print('Learning model could not be stored to file: %s' % model_path, sys.stderr)
        success = False
    finally:
        return success


def getLearningModelPath():
    """
    Returns the platform-specific path to the learning model
    :return: string; absolute path to the json file with the serialized learning model
    """
    if os.name == 'nt':
        path = asWindows(os.path.abspath(MODEL_FILE))
    else:
        path = os.path.abspath(MODEL_FILE)
    return path
