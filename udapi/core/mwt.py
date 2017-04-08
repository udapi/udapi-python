"""MWT class represents a multi-word token."""
from udapi.core.dualdict import DualDict


class MWT(object):
    """Class for representing multi-word tokens in UD trees."""
    __slots__ = ['words', 'form', '_misc', 'root']

    def __init__(self, words=None, form=None, misc=None, root=None):
        self.words = words if words is not None else []
        self.form = form
        self._misc = DualDict(misc)
        self.root = root
        for word in self.words:
            word._mwt = self  # pylint: disable=W0212

    @property
    def misc(self):
        """Property for MISC attributes stored as a `DualDict` object.

        See `udapi.core.node.Node` for details.
        """
        return self._misc

    @misc.setter
    def misc(self, value):
        self._misc.set_mapping(value)

    def ord_range(self):
        """Return a string suitable for the first column of CoNLL-U."""
        return "%d-%d" % (self.words[0].ord, self.words[-1].ord)

    def remove(self):
        """Delete this multi-word token (but keep its words)."""
        for word in self.words:
            word._mwt = None  # pylint: disable=W0212
        self.root.multiword_tokens = [tok for tok in self.root.multiword_tokens if tok != self]

    def address(self):
        """Full (document-wide) id of the multi-word token."""
        return self.root.address + '#' + self.ord_range

# TODO: node.remove() should check if the node is not part of any MWT
# TODO: mwt.words.append(node) and node.shift* should check if the MWT does not contain gaps
#       and is still multi-word
# TODO: check if one word is not included in multiple multi-word tokens
