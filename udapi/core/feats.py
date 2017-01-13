"""Feats class for storing morphological features of nodes in UD trees."""
import udapi.core.dualdict

class Feats(udapi.core.dualdict.DualDict):
    """Feats class for storing morphological features of nodes in UD trees.

    See http://universaldependencies.org/u/feat/index.html for the specification of possible
    feature names and values.
    """

    def is_singular(self):
        return self['Number'].find('Sing') != -1

    def is_plural(self):
        return self['Number'].find('Plur') != -1
