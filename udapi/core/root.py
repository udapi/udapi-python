#!/usr/bin/env python

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
    Class for representing root nodes (technical roots) in Universal Dependency trees

    """
    __slots__ = [
        "_sent_id",
        "sentence",
        "_zone",
        "_bundle",
        "_children",  # ord-ordered list of child nodes
        "_aux"        # other technical attributes
    ]

    def __init__(self, data=None):
        # Initialize data if not given
        if data is None:
            data = dict()

        # Call constructor of the parent object.
        super(Root, self).__init__(data)

        self._sent_id = None
        self._children = []
        self._aux = dict()
        self._aux['descendants'] = []
        self._bundle = None

        for name in data:
            setattr(self, name, data[name])

        for name in Node.__slots__:
            try:
                getattr(self, name)
            except:
                setattr(self, name, '_')

    @property
    def sent_id(self):
        return self._sent_id

    @sent_id.setter
    def sent_id(self, sent_id):
        self._sent_id = sent_id

    @property
    def aux(self):
        return self._aux

    @property
    def zone(self):
        return self._zone

    def set_zone(self,zone):
        """specify which zone the root belongs to"""
        if self.bundle:
            self.bundle._check_zone(self,zone)
        self._zone = zone

    @property
    def bundle(self):
        return self._bundle

    # TODO: this enumeration looks silly, can we code the multiple 'read-only attributes' more cleverly?
    
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
    def feats(self):
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



    def dep(self):
        return None



    @property
    def children(self):
        return self._children


    @property
    def parent(self):
        return None

    def set_parent( self, new_parent ):

        raise RuntimeException('technical root cannot be hanged below a node')


    def descendants(self):
        return self._aux['descendants']

    def is_descendant_of(self,node):
        return False


    def is_root(self):
        """returns True for all Root instances"""
        return True

    def remove(self):
        """remove the whole tree from its bundle"""
        self.bundle.trees = [root for root in self.bundle.trees if root==self]

    def shift(self, reference_node, after=0, move_subtree=0, reference_subtree=0):
        raise RuntimeException('technical root cannot be shifted as it is always the first node')

    def address(self):
        """full (document-wide) id of the root"""
        id = self.bundle.id
        if self.zone:
            id = id + "/" + self.zone
        
