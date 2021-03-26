"""MWT class represents a multi-word token."""
from udapi.core.dualdict import DualDict


class MWT(object):
    """Class for representing multi-word tokens in UD trees."""
    __slots__ = ['words', 'form', '_misc', 'root']

    def __init__(self, words=None, form=None, misc=None, root=None):
        self.words = words if words is not None else []
        self.form = form
        self._misc = DualDict(misc) if misc and misc != '_' else None
        self.root = root
        for word in self.words:
            word._mwt = self  # pylint: disable=W0212

    @property
    def misc(self):
        """Property for MISC attributes stored as a `DualDict` object.

        See `udapi.core.node.Node` for details.
        """
        if self._misc is None:
            self._misc = DualDict()
        return self._misc

    @misc.setter
    def misc(self, value):
        if self._misc is None:
            self._misc = DualDict(value)
        else:
            self._misc.set_mapping(value)

    @property
    def ord_range(self):
        """Return a string suitable for the first column of CoNLL-U."""
        self.words.sort()
        return "%d-%d" % (self.words[0].ord, self.words[-1].ord)

    def remove(self):
        """Delete this multi-word token (but keep its words)."""
        for word in self.words:
            word._mwt = None  # pylint: disable=W0212
        self.root.multiword_tokens.remove(self)

    def address(self):
        """Full (document-wide) id of the multi-word token."""
        return self.root.address + '#' + self.ord_range

# TODO: node.remove() should check if the node is not part of any MWT
# TODO: Document that editing words by mwt.words.append(node), del or remove(node) is not supported
# TODO: Make mwt._words private and provide a setter
# TODO: What to do when mwt.words = []? (It is allowed after mwt=MWT().)
# TODO: words.setter and node.shift* should check if the MWT does not contain gaps
#       and is still multi-word
# TODO: Make sure mwt.words are always sorted (even after node.shift*).
# TODO: Check if one word is not included in multiple multi-word tokens.
