import numpy as np
import scipy.stats as st
import warnings
from GeneralUtil import isNumber, replaceLastCommaWithAnd


class DataAnalyzer(object):
    """
    This class performs data analysis on diagram data
    """
    def __init__(self, ontology):
        """
        DataAnalyzer constructor
        """
        pass

    @staticmethod
    def dist_best_fit(data):
        """
        Finds the distribution that best fits the given data
        :param data: List of data points
        :return: (string, list); name of the distribution that best fits the give data e.g., 'norm'; None if not found,
        and list with the parameters of the distribution
        """
        check_dists = ['gamma', 'beta', 'rayleigh', 'norm', 'pareto']
        best_dist = None
        best_params = []
        best_sse = float('inf')
        if data and all(isNumber(n) for n in data):
            x = np.arange(len(data))
            y = np.array(data)
            for dname in check_dists:
                try:
                    dist = getattr(st, dname)
                    with warnings.catch_warnings():
                        warnings.filterwarnings('ignore')
                        params = dist.fit(y)  # Fit current distribution to data and fetch its parameters
                        args = params[: -2]
                        loc = params[-2]
                        scale = params[-1]
                        pdf = dist.pdf(x, *args, loc=loc, scale=scale)  # Probability Density Function
                        sse = np.sum(np.power(y - pdf, 2.0))  # Sum of squared errors
                        if sse < best_sse:  # SSE is smaller -> better distribution found
                            best_sse = sse
                            best_dist = dname
                            best_params = params
                except Exception as e:
                    warnings.warn("Exception occurred while fitting data to %s distribution: %s") % (dname, str(e))
        return best_dist, best_params

    @staticmethod
    def dist_to_string(dname, params):
        """
        Returns a textual representation of the given distribution and its statistics
        :param dname: string; a distribution name as given by SciPy e.g. 'norm'
        :param params: parameters of the distribution
        :return: string; textual information about the distribution
        """
        check_dists = {'gamma': 'Gamma', 'beta': 'Beta', 'rayleigh': 'Rayleigh', 'norm': 'Normal', 'pareto': 'Pareto'}
        if dname in check_dists:
            label = "%s distribution" % check_dists[dname]
        else:
            label = 'Unknown distribution'
        if dname == 'norm':
            mean = params[-2]
            std = params[-1]
            label += " with mean %.2f and  standard deviation %.2f" % (mean, std)
        else:
            label += " with parameters %s" % (replaceLastCommaWithAnd(", ".join([str(round(p, 2)) for p in params])))
        return label
