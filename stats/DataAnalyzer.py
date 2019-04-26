import numpy as np
import scipy.stats as st
import warnings
from GeneralUtil import isNumber, replaceLastCommaWithAnd
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler


class DataAnalyzer(object):
    """
    This class performs data analysis on diagram data
    """
    def __init__(self, data):
        """
        DataAnalyzer constructor. Prepares the data set.
        :param data: dict<string; list<float>> IDs of graphic objects and their associated n-dimensional values
        """
        dim = 1 if isNumber(data.values()[0]) else len(data.values()[0])
        x = np.zeros((len(data), dim))  # x.shape == (n_samples, value_dimensions)
        obj_names = []
        for i, b in enumerate(data):
            x[i] = data[b]
            obj_names.append(b)
        self.samples = x
        self.labels = obj_names

    def dist_best_fit(self):
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
        if all(isNumber(n) for row in self.samples for n in row):
            x = np.arange(len(self.samples))
            for dname in check_dists:
                try:
                    dist = getattr(st, dname)
                    with warnings.catch_warnings():
                        warnings.filterwarnings('ignore')
                        params = dist.fit(self.samples)  # Fit current distribution to data and fetch its parameters
                        args = params[: -2]
                        loc = params[-2]
                        scale = params[-1]
                        pdf = dist.pdf(x, *args, loc=loc, scale=scale)  # Probability Density Function
                        sse = np.sum(np.power(self.samples - pdf, 2.0))  # Sum of squared errors
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
            label += " with mean %.2f and standard deviation %.2f" % (mean, std)
        else:
            label += " with parameters %s" % (replaceLastCommaWithAnd(", ".join([str(round(p, 2)) for p in params])))
        return label

    def find_clusters(self):
        """
        Finds clusters of similar valued graphic objects via DBSCAN clustering
        :param data: dict<string; list<float>> IDs of graphic objects and their associated n-dimensional values
        :return: list<list<string>>>, list<string> list of lists; each nested list corresponds to a cluster
        of element IDs. The second lister contains the found noise bars (outliers)
        """
        clusters = []
        outliers = []
        if len(self.samples) == 0:
            return clusters
        x = StandardScaler().fit_transform(self.samples)  # Scale values to zero mean and unit std
        db = DBSCAN(eps=0.3, min_samples=2).fit(x)
        core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
        core_samples_mask[db.core_sample_indices_] = True
        cluster_labels = db.labels_
        cluster_unique_labels = set(cluster_labels)
        clusters_dict = {}
        for c_l in cluster_unique_labels:
            clusters_dict[c_l] = []
        for i, c_label in enumerate(cluster_labels):
            if c_label != -1:
                clusters_dict[c_label].append(self.labels[i])
            else:
                outliers.append(self.labels[i])
        for _, bars in clusters_dict.iteritems():
            if bars:
                clusters.append(bars)
        return clusters, outliers
