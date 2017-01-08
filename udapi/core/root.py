"""Root class represents the technical root node in each tree."""
from udapi.core.node import Node


class Root(Node):
    """
    Class for representing root nodes (technical roots) in UD trees.
    """
    __slots__ = ['_sent_id', '_zone', '_bundle', '_children', '_aux', 'text']

    def __init__(self, data=None):
        # Initialize data if not given
        if data is None:
            data = dict()

        # Call constructor of the parent object.
        super(Root, self).__init__(data)

        self.ord = 0
        self.form = '<ROOT>'
        self.lemma = '<ROOT>'
        self.upostag = '<ROOT>'
        self.xpostag = '<ROOT>'
        self.deprel = '<ROOT>'
        self.misc = None
        self.text = None

        self._parent = None
        self._sent_id = None
        self._zone = None
        self._bundle = None
        self._children = list()
        self._aux = dict()
        self._aux['descendants'] = []

        for name in data:
            setattr(self, name, data[name])

    @property
    def sent_id(self):
        """ID of this tree, stored in the sent_id comment in CoNLL-U."""
        return self._sent_id

    @sent_id.setter
    def sent_id(self, sent_id):
        self._sent_id = sent_id

    @property
    def bundle(self):
        """Bundle which this tree belongs to."""
        return self._bundle

    @bundle.setter
    def bundle(self, bundle):
        self._bundle = bundle

    @property
    def zone(self):
        return self._zone

    @zone.setter
    def zone(self, zone):
        """Specify which zone the root belongs to."""
        if self._bundle:
            self._bundle.check_zone(zone)
        self._zone = zone

    @property
    def children(self):
        return self._children

    @children.setter
    def children(self, children):
        self._children = children

    @property
    def aux(self):
        return self._aux

    @aux.setter
    def aux(self, value):
        self._aux = value

    @property
    def parent(self):
        return None

    @parent.setter
    def parent(self, _):
        raise AttributeError('The technical root cannot have a parent.')

    def descendants(self):
        """
        Return a list of all descendants of the current node.

        The nodes are sorted by their ord.
        This root-specific implementation returns all the nodes in the tree
        except the root itself.

        :return: A list of descendant nodes.
        :rtype: list
        """
        return self._aux['descendants']

    def is_descendant_of(self, node):
        return False

    def is_root(self):
        """
        Returns True for all Root instances.

        """
        return True

    def remove(self):
        """
        Remove the whole tree from its bundle

        """
        self.bundle.trees = [
            root for root in self.bundle.trees if root == self]

    def shift(self,
              reference_node, after=0, move_subtree=0, reference_subtree=0):
        raise Exception(
            'Technical root cannot be shifted as it is always the first node')

    def address(self):
        """Full (document-wide) id of the root."""
        return self._bundle.bundle_id + ('/' + self.zone if self.zone else '')
