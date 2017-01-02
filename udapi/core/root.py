from udapi.core.node import Node


class TreexException(Exception):
    """
    Common ancestor for Treex exception.

    """

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return 'TREEX-FATAL: ' + self.__class__.__name__ + ': ' + self.message


class RuntimeException(TreexException):
    """
    Block runtime exception.

    """

    def __init__(self, text):
        TreexException.__init__(self, text)


class Root(Node):
    """
    Class for representing root nodes (technical roots) in Universal Dependency trees.

    """
    __slots__ = list()
    __slots__.append('_sent_id')   # A sentence identifier.
    __slots__.append('_zone')      # A zone.
    __slots__.append('_bundle')    # A bundle.
    __slots__.append('_children')  # An ord-ordeded list of children nodes.
    __slots__.append('_aux')       # Other technical attributes.

    def __init__(self, data=None):
        # Initialize data if not given
        if data is None:
            data = dict()

        # Call constructor of the parent object.
        super(Root, self).__init__(data)

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
        return self._sent_id

    @sent_id.setter
    def sent_id(self, sent_id):
        self._sent_id = sent_id

    @property
    def zone(self):
        return self._zone

    @zone.setter
    def zone(self, zone):
        """
        Specify which zone the root belongs to

        """
        if self.bundle:
            self.bundle.check_zone(self, zone)

        self._zone = zone

    @property
    def bundle(self):
        return self._bundle

    @bundle.setter
    def bundle(self, bundle):
        self._bundle = bundle

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

    # TODO: this enumeration looks silly, can we code the multiple 'read-only
    # attributes' more cleverly?

    @property
    def ord(self):
        return 0

    @property
    def form(self):
        return '<ROOT>'

    @property
    def lemma(self):
        return '<ROOT>'

    @property
    def upostag(self):
        return '<ROOT>'

    @property
    def xpostag(self):
        return '<ROOT>'

    @property
    def raw_feats(self):
        return '<ROOT>'

    @property
    def deprel(self):
        return '<ROOT>'

    @property
    def deps(self):
        return '<ROOT>'

    @property
    def misc(self):
        return '<ROOT>'

    @property
    def feats(self):
        return '<ROOT>'

    @property
    def parent(self):
        return None

    @parent.setter
    def parent(self, new_parent):
        raise AttributeError('The technical root cannot have a parent.')

    def descendants(self):
        """
        Return a list of all descendants of the current node, i.e. the all non-technical
        node from the dependency tree.

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

    def shift(self, reference_node, after=0, move_subtree=0, reference_subtree=0):
        raise RuntimeException(
            'Technical root cannot be shifted as it is always the first node')

    def address(self):
        """
        Full (document-wide) id of the root.

        """
        partial_ids = []

        if self.bundle:
            partial_ids.append(self.bundle.id)

        if self.zone:
            partial_ids.append(self.zone)

        return '/'.join(partial_ids)
