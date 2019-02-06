import json
import os
from dialog.model.Key import *
from dialog.model.Vote import *
from GeneralUtil import asWindows

MODEL_FILE = '../storage/votes.json'


def loadLearningModel():
    """
    Load the current learning model from a serialized file on disk
    :return: dict<Key, list<Vote>>
    """
    import ast
    model_path = getLearningModelPath()
    model = {}
    try:
        with open(model_path, 'a+') as f:
            model_serialized = json.load(f)
            for key_str, vote_list_dict in model_serialized.iteritems():
                k = Key()
                key_dict = ast.literal_eval(key_str)
                k.from_dict(key_dict)
                votes = []
                for vote_dict in vote_list_dict:
                    v = Vote()
                    v.from_dict(vote_dict)
                    votes.append(v)
                model[k] = votes
    except Exception:
        import sys
        print('Learning model could not be loaded from path: %s' % model_path, sys.stderr)
    return model


def saveLearningModel(model):
    """
    Serialize and store a learning model to disk
    :param model: A dict<Key, list<Vote>> containing the learning model
    :return: True on successful storage; False otherwise
    """
    model_path = getLearningModelPath()
    success = True
    try:
        with open(model_path, 'w') as f:
            model_dict = {}
            for key, vote_list in model.iteritems():
                vote_dict_list = []
                key_str = str(key)
                for v in vote_list:
                    vote_dict_list.append(v.to_dict())
                model_dict[key_str] = vote_dict_list
            json.dump(model_dict, f)
    except Exception:
        import sys
        print('Learning model could not be stored to file: %s' % model_path, sys.stderr)
        success = False
    finally:
        return success


def clearLearningModel():
    """
    Clear the persisted learning model
    :return: True on success; False otherwise
    """
    model = {}
    return saveLearningModel(model)


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
