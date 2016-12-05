#!/usr/bin/env python

from operator import attrgetter

import codecs
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

# ----- nasledujici jen kvuli tomu, abych mohl poustet benchmark (pri prevesovani nastavaji cykly a ocekava se RuntimeException) ---

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


class Node(object):
    """Class for representing non-root nodes in Universal Dependency trees"""

    __slots__ = [
                   # (A) features following the CoNLL-U documentation
                  "ord",      # Word index, integer starting at 1 for each new sentence; may be a range for tokens with multiple words.
                  "form",     # Word form or punctuation symbol.
                  "lemma",    # Lemma or stem of word form.
                  "upostag",  # Universal part-of-speech tag drawn from our revised version of the Google universal POS tags.
                  "xpostag",  #  Language-specific part-of-speech tag; underscore if not available.
                  "feats",    # List of morphological features from the universal feature inventory or from a defined language-specific extension; underscore if not available.
                  "head",     # Head of the current token, which is either a value of ID or zero (0).
                  "deprel",   # Universal Stanford dependency relation to the HEAD (root iff HEAD = 0) or a defined language-specific subtype of one.
                  "deps",     # List of secondary dependencies (head-deprel pairs).
                  "misc",     # Any other annotation.

                   # (B) udapi-specific extra features

                  "_parent",  # parent node
                  "_children",# ord-ordered list of child nodes
                  "_aux"     # other technical attributes

    ]

    def __init__(self, data=None):
        if data is None:
            data = dict()

        self._parent = None
        self._children = []
        self._aux = {}

        for name in data:
            setattr(self,name,data[name])

        for name in Node.__slots__:
            try:
                getattr(self,name)
            except:
                setattr(self,name,'_')

    def __str__(self):
        """
        Pretty print of the Node object.

        :return: A pretty textual description of the Node.

        """
        return "<%d, %s, %d, %s>" % (self.ord, self.form, self.parent.ord, self.deprel)

    @property
    def children(self):
        return self._children

    @property
    def parent(self):
        return self._parent

    def set_parent( self, new_parent ):

        if self.parent == new_parent:
            return

        elif self == new_parent:
            raise RuntimeException('setting the parent would lead to a loop: '+str(self))

        if self._parent:
            old_parent = self.parent

            climbing_node = new_parent

            while not climbing_node.is_root:
                if climbing_node == self:
                    raise RuntimeException('setting the parent would lead to a loop: '+str(self))
                climbing_node = climbing_node.parent

            old_parent._children = [node for node in old_parent._children if node != self ]

        self._parent =new_parent
        new_parent._children = sorted( new_parent._children + [self], key=attrgetter('ord') )



    def descendants(self):
        if self.is_root():
            return self._aux['descendants']
        else:
            return sorted( self._unordered_descendants_using_children() )

    def is_descendant_of(self,node):
        climber = self.parent
        while climber:
            if climber==node:
                    return True
            climber = climber.parent
            return False


    def create_child(self):
        new_node = Node()
        new_node.ord = len(self.root()._aux['descendants'])+1
        self.root()._aux['descendants'].append(new_node)
        self._children.append(new_node)
        new_node._parent = self
        return new_node


    def _unordered_descendants_using_children(self):
        descendants = [self]
        for child in self.children:
            descendants.extend(child._unordered_descendants_using_children())
        return descendants

    def root(self):
        """climbs up to the root and returns it"""
        node = self

        while (node.parent):
            node = node.parent
        return node

    def is_root(self):
        """returns False for all Node instances, irrespectively of whether is has a parent or not"""
        return False

    def _update_ordering(self):
         """ update the ord attribute in all nodes and update the list or descendants stored in the tree root (after node removal or addition) """
         self.info("UPDATE start")

         root = self.root()

         descendants = sorted( [node for node in root._unordered_descendants_using_children() if node != root] ,
                               key=attrgetter('ord') )


         self.info ("descendanti podle children: "+(" ".join([node.form+"-"+str(node.ord) for node in descendants])))


         root._aux['descendants'] = descendants

         ord = 1
         for node in descendants:
             node.ord = ord
             ord += 1

         self.info ("descendanti podle children: "+(" ".join([node.form+"-"+str(node.ord) for node in self.root().descendants()])))

         self.info("UPDATE hotovo")


    def remove(self):

        self.parent._children = [ child for child in self.parent._children if child != self ]
        self.parent._update_ordering()


    def shift(self, reference_node, after=0, move_subtree=0, reference_subtree=0):

        self.info("SHIFT")

        nodes_to_move = [self]

        if move_subtree:
            nodes_to_move.extend(self.descendants())

        reference_ord = reference_node.ord

        if reference_subtree:
            for node in [n for n in reference_node.descendants() if n != self]:
                if (after and node.ord > reference_ord) or (not after and node.ord < reference_ord):
                    reference_ord = node.ord
                    try:
                        self.info("last reference node: "+node.upostag)
                    except:
                        pass

        self.info("final reference ord "+str(reference_ord))

        common_delta = 0.5 if after else -0.5

        for node_to_move in nodes_to_move:
            node_to_move.ord = reference_ord + common_delta + (node_to_move.ord-self.ord)/100000.  # TODO: can we use some sort of epsilon instead of choosing a silly upper bound for out-degree?
            self.info("NEW ORD OF x: "+str(node_to_move.ord))

        self._update_ordering()



    def shift_after(self, reference_node):
        self.shift(reference_node,after=1,move_subtree=0,reference_subtree=0)

    def shift_subtree_after(self, reference_node):
        self.shift(reference_node,after=1,move_subtree=1,reference_subtree=0)

#    def shift(self, reference_node, after=0, move_subtree=0, reference_subtree=0):

    def shift_after_node(self, reference_node):
        self.shift(reference_node, after=1, move_subtree=1, reference_subtree=0)

    def shift_before_node(self, reference_node):
        self.shift(reference_node, after=0, move_subtree=1, reference_subtree=0)

    def shift_after_subtree(self, reference_node, without_children=0):
        self.shift(reference_node, after=1, move_subtree=1-without_children, reference_subtree=1)

    def shift_before_subtree(self, reference_node, without_children=0):
        self.shift(reference_node, after=0, move_subtree=1-without_children, reference_subtree=1)


    def prev_node(self):
        new_ord = self.ord - 1
        if new_ord < 0:
            return None
        if new_ord == 0:
            return self.root()
        return self.root()._aux['descendants'][self.ord - 1]

    def next_node(self):
        # Note that all_nodes[n].ord == n+1
        try:
            return self.root()._aux['descendants'][self.ord]
        except IndexError:
            return None

    def info(self,message):
        import sys
        sys.stderr.write("INFO "+message+"\n")

    def address(self):
        """full (document-wide) id of the node"""
        return self.root.address()+"#".self.ord

