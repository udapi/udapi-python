"""Node class represents a node in UD trees."""
from udapi.block.write.textmodetrees import TextModeTrees

class Node(object):
    """Class for representing nodes in Universal Dependency trees."""

    # TODO: Benchmark memory and speed of slots vs. classic dict.
    # With Python 3.5 split dict, slots may not be better.
    # TODO: Should not we include __weakref__ in slots?
    __slots__ = [
        # Word index, integer starting at 1 for each new sentence.
        'ord',
        'form',    # Word form or punctuation symbol.
        'lemma',   # Lemma of word form.
        'upostag', # Universal PoS tag
        'xpostag', # Language-specific part-of-speech tag; underscore if not available.
        'deprel',  # UD dependency relation to the HEAD (root iff HEAD = 0).
        'misc',    # Any other annotation.

        # Enhanced dependencies (head-deprel pairs) in their original CoNLLU format.
        '_raw_deps',
        # Deserialized enhanced dependencies in a list of {parent, deprel} dicts.
        '_deps',
        # Morphological features in their original CoNLLU format.
        '_raw_feats',
        # Deserialized morphological features stored in a dict (feature -> value).
        '_feats',
        '_parent',     # Parent node.
        '_children',   # Ord-ordered list of child nodes.
        '_mwt',        # multi-word token in which this word participates
    ]

    def __init__(self, data=None):
        """Create new node and initialize its attributes with data."""
        # Initialization of the (A) list.
        self.ord = None
        self.form = None
        self.lemma = None
        self.upostag = None
        self.xpostag = None
        self.deprel = None
        self.misc = None

        # Initialization of the (B) list.
        self._raw_deps = '_'
        self._deps = None
        self._raw_feats = '_'
        self._feats = None
        self._parent = None
        self._children = list()
        self._mwt = None

        # If given, set the node using data from arguments.
        if data is not None:
            for name in data:
                setattr(self, name, data[name])

    def __str__(self):
        """Pretty print of the Node object."""
        parent_ord = None
        if self.parent is not None:
            parent_ord = self.parent.ord
        return "<%d, %s, %s, %s>" % (self.ord, self.form, parent_ord, self.deprel)

    @property
    def raw_feats(self):
        """String serialization of morphological features as stored in CoNLL-U files.

        After the access to the raw morphological features,
        provide the serialization of the features if they were deserialized already.
        """
        if self._feats is not None:
            serialized_features = []
            for feature in sorted(self._feats):
                serialized_features.append('%s=%s' % (feature, self._feats[feature]))
            self._raw_feats = '|'.join(serialized_features)
        return self._raw_feats

    @raw_feats.setter
    def raw_feats(self, value):
        """Set serialized morphological features (the new value is a string).

        When updating raw morphological features,
        delete the current version of the deserialized feautures.
        """
        self._raw_feats = str(value)
        self._feats = None

    @property
    def raw_deps(self):
        """String serialization of enhanced dependencies as stored in CoNLL-U files.

        After the access to the raw enhanced dependencies,
        provide the serialization if they were deserialized already.
        """
        if self._deps is not None:
            serialized_deps = []
            for secondary_dependence in self._deps:
                serialized_deps.append('%d:%s' % (secondary_dependence[
                    'parent'].ord, secondary_dependence['deprel']))

            serialized_deps = '|'.join(serialized_deps)
            self._raw_deps = serialized_deps

        return self._raw_deps

    @raw_deps.setter
    def raw_deps(self, value):
        """Set serialized enhanced dependencies (the new value is a string).

        When updating raw secondary dependencies,
        delete the current version of the deserialized data.
        """
        self._raw_deps = str(value)
        self._deps = None

    @property
    def feats(self):
        """Return morphological features as a Python dict.

        After the first access to the morphological features,
        provide the deserialization of the features and save features to the dict.
        """
        if self._feats is None:
            self._feats = dict()
            for raw_feature in self._raw_feats.split('|'):
                feature, value = raw_feature.split('=')
                self._feats[feature] = value

        return self._feats

    @feats.setter
    def feats(self, value):
        """Set deserialized morphological features (the new value is a dict)."""
        self._feats = value

    @property
    def deps(self):
        """Return enhanced dependencies as a Python list of dicts.

        After the first access to the enhanced dependencies,
        provide the deserialization of the raw data and save deps to the list.
        """
        if self._deps is None:
            # Obtain a list of all nodes in the dependency tree.
            nodes = [self.root] + self.root.descendants()

            # Create a list of secondary dependencies.
            self._deps = list()

            if self._raw_deps == '_':
                return self._deps

            for raw_dependency in self._raw_deps.split('|'):
                head, deprel = raw_dependency.split(':')
                parent = nodes[int(head)]
                self._deps.append({'parent': parent, 'deprel': deprel})

        return self._deps

    @deps.setter
    def deps(self, value):
        """Set deserialized enhanced dependencies (the new value is a list of dicts)."""
        self._deps = value

    @property
    def parent(self):
        """Return dependency parent (head) node."""
        return self._parent

    @parent.setter
    def parent(self, new_parent):
        """Set a new dependency parent node.

        Check if the parent assignment is valid (no cycles) and assign
        a new parent (dependency head) for the current node.
        If the node had a parent, it is detached first
        (from the list of original parent's children).
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
                raise Exception('Setting the parent would lead to a loop: %s' % self)
            climbing_node = climbing_node.parent

        # Remove the current Node from the children of the old parent.
        if self.parent:
            self.parent._children = [node for node in self.parent.children if node != self]

        # Set the new parent.
        self._parent = new_parent

        # Append the current node the the new parent children.
        new_parent._children = sorted(new_parent.children + [self], key=lambda child: child.ord)

    @property
    def children(self):
        """Return a list of dependency children (direct dependants) nodes."""
        return self._children

    @property
    def root(self):
        """Return the (technical) root node of the whole tree."""
        node = self
        while node.parent:
            node = node.parent
        return node

    def descendants(self):
        """Return a list of all descendants of the current node.

        The nodes are sorted by their ord.
        """
        return sorted(self.unordered_descendants(), key=lambda node: node.ord)

    def is_descendant_of(self, node):
        """Is the current node a descendant of the node given as argument?"""
        climber = self.parent
        while climber:
            if climber == node:
                return True
            climber = climber.parent
        return False

    def create_child(self):
        """Create and return a new child of the current node."""
        new_node = Node()
        new_node.ord = len(self.root._descendants) + 1
        self.root._descendants.append(new_node)
        self.children.append(new_node)
        new_node.parent = self
        return new_node

    # TODO: make private: _unordered_descendants
    def unordered_descendants(self):
        """Return a list of all descendants in any order."""
        descendants = [self]
        for child in self.children:
            descendants.extend(child.unordered_descendants())
        return descendants

    def is_root(self):
        """Is the current node a (technical) root?

        Returns False for all Node instances, irrespectively of whether is has a parent or not.
        True is returned only by instances of udapi.core.root.Root.
        """
        return False

    # TODO make private: _udpate_ordering
    def update_ordering(self):
        """Update the ord ord attribute in all nodes.

        Update also the list or descendants stored in the tree root.
        This method is automatically called after node removal or addition.
        """
        root = self.root
        descendants = [node for node in root.unordered_descendants() if node != root]
        descendants = sorted(descendants, key=lambda node: node.ord)
        root._descendants = descendants
        for (new_ord, node) in enumerate(descendants):
            node.ord = new_ord + 1

    def remove(self):
        """Delete this node and all its descendants."""
        self.parent.children = [child for child in self.parent.children if child != self]
        self.parent.update_ordering()

    # TODO: make private: _shift
    def shift(self, reference_node, after=0, move_subtree=0, reference_subtree=0):
        """Internal method for changing word order."""
        nodes_to_move = [self]

        if move_subtree:
            nodes_to_move.extend(self.descendants())

        reference_ord = reference_node.ord

        if reference_subtree:
            for node in [n for n in reference_node.descendants() if n != self]:
                if (after and node.ord > reference_ord) or (not after and node.ord < reference_ord):
                    reference_ord = node.ord

        common_delta = 0.5 if after else -0.5

        # TODO: can we use some sort of epsilon instead of choosing a silly
        # upper bound for out-degree?
        for node_to_move in nodes_to_move:
            node_to_move.ord = reference_ord + common_delta + \
                (node_to_move.ord - self.ord) / 100000.

        self.update_ordering()

    # TODO delete
    def shift_after(self, reference_node):
        self.shift(reference_node, after=1, move_subtree=0, reference_subtree=0)

    # TODO delete
    def shift_subtree_after(self, reference_node):
        self.shift(reference_node, after=1, move_subtree=1, reference_subtree=0)

    # TODO add without_children kwarg
    def shift_after_node(self, reference_node):
        """Shift this node after the reference_node."""
        self.shift(reference_node, after=1, move_subtree=1, reference_subtree=0)

    def shift_before_node(self, reference_node):
        """Shift this node after the reference_node."""
        self.shift(reference_node, after=0, move_subtree=1, reference_subtree=0)

    def shift_after_subtree(self, reference_node, without_children=0):
        """Shift this node (and its subtree) after the subtree rooted by reference_node.

        Args:
        without_children: shift just this node without its subtree?
        """
        self.shift(reference_node, after=1, move_subtree=not without_children, reference_subtree=1)

    def shift_before_subtree(self, reference_node, without_children=0):
        """Shift this node (and its subtree) before the subtree rooted by reference_node.

        Args:
        without_children: shift just this node without its subtree?
        """
        self.shift(reference_node, after=0, move_subtree=not without_children, reference_subtree=1)

    def prev_node(self):
        """Return the previous node according to word order."""
        new_ord = self.ord - 1
        if new_ord < 0:
            return None
        if new_ord == 0:
            return self.root
        return self.root._descendants[self.ord - 1]

    def next_node(self):
        """Return the following node according to word order."""
        # Note that all_nodes[n].ord == n+1
        try:
            return self.root._descendants[self.ord]
        except IndexError:
            return None

    def is_leaf(self):
        """Is this node a leaf, ie. a node without any children?"""
        return not self.children

    def get_attrs(self, attrs, undefs=None):
        """Return multiple attributes, possibly subsitituting empty ones.

        Args:
        attrs: A list of attribute names, e.g. ['form', 'lemma'].
        undefs: A value to be used instead of None for empty (undefined) values.
        """
        values = [getattr(self, name) for name in attrs]
        if undefs is not None:
            values = [x if x is not None else undefs for x in values]
        return values

    def compute_sentence(self):
        """Return a string representing this subtree's text (detokenized).

        Compute the string by concatenating forms of nodes
        (words and multi-word tokens) and joining them with a single space,
        unless the node has SpaceAfter=No in its misc.
        If called on root this method returns a string suitable for storing
        in root.text (but it is not stored there automatically).

        Technical detail:
        If called on root, the root's form (<ROOT>) is not included in the string.
        If called on non-root nodeA, nodeA's form is included in the string,
        i.e. internally descendants(add_self=True) is used.
        """
        string = ''
        # TODO: use multi-word tokens instead of words where possible.
        # TODO: self.descendants(add_self=not self.is_root()):
        for node in self.descendants():
            string += node.form
            if node.misc.find('SpaceAfter=No') == -1:
                string += ' '
        return string

    def print_subtree(self, **kwargs):
        """Print ASCII visualization of the dependency structure of this subtree.

        This method is useful for debugging.
        Internally udapi.block.write.textmodetrees.TextModeTrees is used for the printing.
        All keyword arguments of this method are passed to its constructor,
        so you can use e.g.:
        files: to redirect sys.stdout to a file
        indent: to have wider trees
        attributes: to override the default list 'form,upostag,deprel'
        See TextModeTrees for details and other parameters.
        """
        TextModeTrees(**kwargs).process_tree(self)

    def address(self):
        """Return full (document-wide) id of the node.

        For non-root nodes, the general address format is:
        node.bundle.bundle_id + '/' + node.root.zone + '#' + node.ord,
        e.g. s123/en_udpipe#4. If zone is empty, the slash is excluded as well,
        e.g. s123#4.
        """
        return '%s#%d' % (self.root.address(), self.ord)

    @property
    def multiword_token(self):
        """Return the multi-word token which includes this node, or None.

        If this node represents a (syntactic) word which is part of a multi-word token,
        this method returns the instance of udapi.core.mwt.MWT.
        If this nodes is not part of any multi-word token, this method returns None.
        """
        return self._mwt
