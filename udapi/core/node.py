#!/usr/bin/env python

import logging


class TreexException(Exception):
    """
    Common ancestor for Treex exception

    """
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return 'TREEX-FATAL: ' + self.__class__.__name__ + ': ' + self.message


class RuntimeException(TreexException):
    """
    Block runtime exception

    """
    def __init__(self, text):
        TreexException.__init__(self, text)


class Node(object):
    """
    Class for representing non-root nodes in Universal Dependency trees.

    """

    __slots__ = list()

    # (A) Features following the CoNLL-U documentation:
    __slots__.append('_ord')        # Word index, integer starting at 1 for each new sentence.
    __slots__.append('_form')       # Word form or punctuation symbol.
    __slots__.append('_lemma')      # Lemma or stem of word form.
    __slots__.append('_upostag')    # Universal POS tag drawn from our revised version of the Google UPOS tags.
    __slots__.append('_xpostag')    # Language-specific part-of-speech tag; underscore if not available.
    __slots__.append('_raw_feats')  # List of morphological features.
    __slots__.append('_head')       # Head of the current token, which is either a value of ID or zero (0).
    __slots__.append('_deprel')     # Universal Stanford dependency relation to the HEAD (root iff HEAD = 0).
    __slots__.append('_deps')       # List of secondary dependencies (head-deprel pairs).
    __slots__.append('_misc')       # Any other annotation.

    # (B) Udapi-specific extra features:
    __slots__.append('_feats')      # A serialization of the morphological features, as they appear in conllu files.
    __slots__.append('_parent')     # Parent node.
    __slots__.append('_children')   # Ord-ordered list of child nodes.
    __slots__.append('_aux')        # Other technical attributes.

    def __init__(self, data=None):
        if data is None:
            data = dict()

        # Initialization of the (A) list.
        self._ord = 0
        self._form = '_'
        self._lemma = '_'
        self._upostag = '_'
        self._xpostag = '_'
        self._raw_feats = '_'
        self._head = '_'
        self._deprel = '_'
        self._deps = '_'
        self._misc = '_'

        # Initialization of the (B) list.
        self._feats = None
        self._parent = None
        self._children = list()
        self._aux = dict()

        # If given, set the node using data from arguments.
        for name in data:
            setattr(self, name, data[name])

    def __str__(self):
        """
        Pretty print of the Node object.

        :return: A pretty textual description of the Node.

        """
        return "<%d, %s, %d, %s>" % (self.ord, self.form, self.parent.ord, self.deprel)

    @property
    def ord(self):
        return self._ord

    @ord.setter
    def ord(self, value):
        self._ord = int(value)

    @property
    def form(self):
        return self._form

    @form.setter
    def form(self, value):
        self._form = value

    @property
    def lemma(self):
        return self._lemma

    @lemma.setter
    def lemma(self, value):
        self._lemma = value

    @property
    def upostag(self):
        return self._upostag

    @upostag.setter
    def upostag(self, value):
        self._upostag = value

    @property
    def xpostag(self):
        return self._xpostag

    @xpostag.setter
    def xpostag(self, value):
        self._xpostag = value

    @property
    def raw_feats(self):
        """
        After the access to the raw morphological feature set,
        provide the serialization of the features if they were deserialized already.

        :return: A raw string with morphological features, as stored in the conllu files.
        :rtype: str

        """
        if self._feats is not None:
            serialized_features = []
            for feature in sorted(self._feats):
                serialized_features.append('%s=%s' % (feature, self._feats[feature]))

            serialized_features = '|'.join(serialized_features)
            self._raw_feats = serialized_features

        return self._raw_feats

    @raw_feats.setter
    def raw_feats(self, value):
        """
        When updating raw morphological features, delete the current version of the deserialized feautures.

        :param value: A new raw morphologial feratures.

        """
        self._raw_feats = str(value)
        self._feats = None

    @property
    def head(self):
        return self._head

    @head.setter
    def head(self, value):
        self._head = int(value)

    @property
    def deprel(self):
        return self._deprel

    @deprel.setter
    def deprel(self, value):
        self._deprel = value

    @property
    def deps(self):
        return self._deps

    @deps.setter
    def deps(self, value):
        self._deps = value

    @property
    def misc(self):
        return self._misc

    @misc.setter
    def misc(self, value):
        self._misc = value

    @property
    def feats(self):
        """
        After the first access to the morphological feature set,
        provide the deserialization of the features and save features to the dict.

        :return: A dict with morphological features.
        :rtype: dict

        """
        if self._feats is None:
            self._feats = dict()
            for raw_feature in self._raw_feats.split('|'):
                feature, value = raw_feature.split('=')
                self._feats[feature] = value

        return self._feats

    @feats.setter
    def feats(self, value):
        self._feats = value

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, new_parent):
        """
        Check if the parent assignment is valid (no cycles) and assign
        a new parent (dependency head) for the current node.
        If the node had a parent, it is detached first
        (from the list of original parent's children).

        :param new_parent: A parent Node object.

        """
        # If the parent is already assigned, return.
        if self.parent == new_parent:
            return

        # The node itself couldn't be assigned as a parent.
        if self == new_parent:
            raise ValueError('Could not set the node itself as a parent: %s' % self)

        # Check if the current Node is not an antecedent of the new parent.
        climbing_node = new_parent
        while not climbing_node.is_root:
            if climbing_node == self:
                raise RuntimeException('Setting the parent would lead to a loop: %s' % self)

            climbing_node = climbing_node.parent

        # Remove the current Node from the children of the old parent.
        if self.parent:
            self.parent.children = [node for node in self.parent.children if node != self]

        # Set the new parent.
        self._parent = new_parent

        # Append the current node the the new parent children.
        new_parent.children = sorted(new_parent.children + [self], key=lambda child: child.ord)

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
        self._aux = int(value)

    @property
    def root(self):
        """
        Climbs up to the root and returns it.

        :return: A root node.
        :rtype: Root

        """
        node = self
        while node.parent:
            node = node.parent

        return node

    def descendants(self):
        """
        Return a list of all descendants of the current node.

        :return: A list of descendant nodes.
        :rtype: list

        """
        if self.is_root():
            return self._aux['descendants']
        else:
            return sorted(self.unordered_descendants_using_children())

    def is_descendant_of(self, node):
        """
        Return true if the given node is a descendant of the current Node.

        :param node: A candidate descendant.
        :return: True if an input node is a descendant of the current Node.
        :rtype: bool

        """
        climber = self.parent
        while climber:
            if climber == node:
                return True

            climber = climber.parent

        return False

    def create_child(self):
        """
        Create a new child of the current node.

        :return: A new created Node.
        :rtype: Node

        """
        new_node = Node()
        new_node.ord = len(self.root.aux['descendants']) + 1
        self.root.aux['descendants'].append(new_node)
        self.children.append(new_node)
        new_node.parent = self
        return new_node

    def unordered_descendants_using_children(self):
        """
        FIXME

        :return:
        :type: list

        """
        descendants = [self]
        for child in self.children:
            descendants.extend(child.unordered_descendants_using_children())
        return descendants

    def is_root(self):
        """
        Returns False for all Node instances, irrespectively of whether is has a parent or not.

        """
        return False

    def update_ordering(self):
        """
        Update the ord attribute in all nodes and update the list or descendants stored in the
        tree root (after node removal or addition)

        """
        root = self.root
        descendants = [node for node in root.unordered_descendants_using_children() if node != root]
        descendants = sorted(descendants, key=lambda descendant: descendant.ord)

        root.aux['descendants'] = descendants

        for (new_ord, node) in enumerate(descendants):
            node.ord = new_ord + 1

    def remove(self):
        """
        FIXME

        :return:

        """
        self.parent.children = [child for child in self.parent.children if child != self]
        self.parent.update_ordering()

    def shift(self, reference_node, after=0, move_subtree=0, reference_subtree=0):
        """
        FIXME

        :param reference_node:
        :param after:
        :param move_subtree:
        :param reference_subtree:
        :return:

        """
        nodes_to_move = [self]

        if move_subtree:
            nodes_to_move.extend(self.descendants())

        reference_ord = reference_node.ord

        if reference_subtree:
            for node in [n for n in reference_node.descendants() if n != self]:
                if (after and node.ord > reference_ord) or (not after and node.ord < reference_ord):
                    reference_ord = node.ord

        common_delta = 0.5 if after else -0.5

        # TODO: can we use some sort of epsilon instead of choosing a silly upper bound for out-degree?
        for node_to_move in nodes_to_move:
            node_to_move.ord = reference_ord + common_delta + (node_to_move.ord-self.ord) / 100000.

        self.update_ordering()

    def shift_after(self, reference_node):
        """
        FIXME

        :param reference_node:
        :return:

        """
        self.shift(reference_node, after=1, move_subtree=0, reference_subtree=0)

    def shift_subtree_after(self, reference_node):
        """
        FIXME

        :param reference_node:
        :return:

        """
        self.shift(reference_node, after=1, move_subtree=1, reference_subtree=0)

    def shift_after_node(self, reference_node):
        """
        FIXME

        :param reference_node:
        :return:

        """
        self.shift(reference_node, after=1, move_subtree=1, reference_subtree=0)

    def shift_before_node(self, reference_node):
        """
        FIXME

        :param reference_node:
        :return:

        """
        self.shift(reference_node, after=0, move_subtree=1, reference_subtree=0)

    def shift_after_subtree(self, reference_node, without_children=0):
        """
        FIXME

        :param reference_node:
        :param without_children:
        :return:

        """
        self.shift(reference_node, after=1, move_subtree=1-without_children, reference_subtree=1)

    def shift_before_subtree(self, reference_node, without_children=0):
        """
        FIXME

        :param reference_node:
        :param without_children:
        :return:

        """
        self.shift(reference_node, after=0, move_subtree=1-without_children, reference_subtree=1)

    def prev_node(self):
        """
        FIXME

        :return:

        """
        new_ord = self.ord - 1
        if new_ord < 0:
            return None
        if new_ord == 0:
            return self.root
        return self.root.aux['descendants'][self.ord - 1]

    def next_node(self):
        """
        FIXME

        :return:

        """
        # Note that all_nodes[n].ord == n+1
        try:
            return self.root.aux['descendants'][self.ord]
        except IndexError:
            return None

    def address(self):
        """
        Full (document-wide) id of the node.

        :return: Full (document-wide) id of the node.
        :rtype: str

        """
        return '%s#%d' % (self.root.address(), self.ord)
