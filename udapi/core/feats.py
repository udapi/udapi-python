"""Feats class for storing morphological features of nodes in UD trees."""
import udapi.core.dualdict


class Feats(udapi.core.dualdict.DualDict):
    """Feats class for storing morphological features of nodes in UD trees.

    See http://universaldependencies.org/u/feat/index.html for the specification of possible
    feature names and values.
    """

    def is_singular(self):
        """Is the grammatical number singular (feats['Number'] contains 'Sing')?"""
        return 'Sing' in self['Number']

    def is_plural(self):
        """Is the grammatical number plural (feats['Number'] contains 'Plur')?"""
        return 'Plur' in self['Number']
