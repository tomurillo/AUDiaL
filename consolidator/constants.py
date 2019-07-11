"""
Consolidator constants
"""

# Prior knowledge: domain tokens that can be ignored (optional)
TOKEN_IGNORE_DOMAIN = ['do', 'does', 'population', 'year', 'years', 'persons', 'people', 'city', 'region', 'province',
                       'area', 'country', 'countries', 'provinces', 'areas', 'cities', 'place', 'places', 'location',
                       'locations', 'bar', 'bars', 'node', 'nodes', 'age', 'live', 'lived', 'tag', 'tagged',
                       'value', 'energy', 'energies', 'information', 'source', 'sources', 'data', 'info', 'consumption',
                       'power', 'generation', 'production', 'like', 'need', 'needed', 'usage', 'number', 'exactly',
                       'exact']

TOKEN_IGNORE_CONSOLIDATION = ["how", "many", "what", "which", "list", "show", "give", "tell"]
