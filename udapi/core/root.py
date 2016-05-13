#!/usr/bin/env python

from udapi.core.node import Node
from operator import attrgetter

import codecs
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

# ----- nasledujici jen kvuli tomu, abych mohl poustet benchmark (pri prevesovani nastavaji cykly a ocekava se RuntimeException) ---


########## co s timhle?

class TreexException(Exception):
    "Common ancestor for Treex exception"
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return 'TREEX-FATAL: ' + self.__class__.__name__ + ': ' + self.message

class RuntimeException(TreexException):
    "Block runtime exception"

    def __init__(self, text):
        TreexException.__init__(self, text)

# ---------------------------------------------------------------------------------------------




class Root(Node):

    """Class for representing root nodes (technical roots) in Universal Dependency trees"""

    __slots__ = [
                  "sent_id",
                  "zone",
                  "_bundle",
                  "_children",# ord-ordered list of child nodes
                  "_aux"     # other technical attributes

    ]


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


    def __init__(self, data={}):

        self._children = []
        self._aux = {}

        for name in data:
            setattr(self,name,data[name])

        for name in Node.__slots__:
            try:
                getattr(self,name)
            except:
                setattr(self,name,'_')

    @property
    def children(self):
        return self._children


    @property
    def parent(self):
        return self._parent

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
        raise RuntimeException('Tree root cannot be removed using root.remove(). Use bundle.remove_tree(zone) instead')


    def shift(self, reference_node, after=0, move_subtree=0, reference_subtree=0):
        raise RuntimeException('technical root cannot be shifted as it is always the first node')

    def info(self,message):
        import sys
        sys.stderr.write("INFO "+message+"\n")

