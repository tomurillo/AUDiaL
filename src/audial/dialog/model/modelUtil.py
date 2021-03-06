import json
import os
from dialog.model.Key import *
from dialog.model.LearningVote import *

MODEL_FILE = 'votes.json'


def loadLearningModel(deserialize=True):
    """
    Load the current learning model from a serialized file on disk
    :param deserialize: Whether to covert the loaded data to model classes (True; default) or keep it as a dict of
    builtin types (False)
    :return: dict<Key, list<LearningVote>>
    """
    model_path = getLearningModelPath()
    model = {}
    try:
        with open(model_path, 'a+') as f:
            model_serialized = json.load(f)
            if deserialize:
                for key_str, vote_list_dict in model_serialized.iteritems():
                    k = Key()
                    key_dict = json.loads(key_str)
                    k.from_dict(key_dict)
                    votes = []
                    for vote_dict in vote_list_dict:
                        v = LearningVote()
                        v.from_dict(vote_dict)
                        votes.append(v)
                    model[k] = votes
            else:
                model = model_serialized
    except Exception as e:
        from warnings import warn
        warn('Learning model could not be loaded from path: %s: %s' % (model_path, str(e)))
    finally:
        return model


def saveLearningModel(model, clear_existing=False):
    """
    Serialize and store a learning model to disk
    :param model: A dict<Key, list<LearningVote>> containing the learning model
    :param clear_existing: Whether to clear the existing learning model (True) or keep it (False; default)
    :return: True on successful storage; False otherwise
    """
    model_path = getLearningModelPath()
    success = True
    try:
        if clear_existing:
            model_dict = {}
        else:
            model_dict = loadLearningModel(deserialize=False)
        with open(model_path, 'w') as f:
            for key, vote_list in model.iteritems():
                vote_dict_list = []
                key_str = str(key)
                for v in vote_list:
                    vote_dict_list.append(v.to_dict())
                model_dict[key_str] = vote_dict_list
            json.dump(model_dict, f)
    except Exception as e:
        from warnings import warn
        warn('Learning model could not be stored to file %s: %s' % (model_path, str(e)))
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
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "../storage", MODEL_FILE))
