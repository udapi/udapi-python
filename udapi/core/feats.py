"""Feats class for storing morphological features of nodes in UD trees."""

class Feats(dict):
    """Feats class for storing morphological features of nodes in UD trees."""

    def __missing__(self, key):
        """Let the default value be an empty string."""
        return ''
