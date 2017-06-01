"""Node class and related classes and functions.

In addition to class `Node`, this module contains class `ListOfNodes`
and function `find_minimal_common_treelet`.
"""
import logging

from udapi.block.write.textmodetrees import TextModeTrees
from udapi.core.dualdict import DualDict
from udapi.core.feats import Feats

# Pylint complains when we access e.g. node.parent._children or root._descendants
# because it does not know that node.parent is the same class (Node)
# and Root is a "friend" class of Node, so accessing underlined attributes is OK and intended.
# Moreover, pylint has false-positive no-member alarms when accessing node.root._descendants
# (pylint thinks node.root returns a Node instance, but actually it returns a Root instance).
# pylint: disable=protected-access,no-member

# 7 instance attributes and 20 public methods are too low limits (CoNLL-U has 10 columns)
# The set of public attributes/properties and methods of Node was well-thought.
# pylint: disable=too-many-instance-attributes,too-many-public-methods


class Node(object):
    """Class for representing nodes in Universal Dependency trees.

    Attributes `form`, `lemma`, `upos`, `xpos` and `deprel` are public attributes of type `str`,
    so you can use e.g. `node.lemma = node.form`.

    `node.ord` is a int type public attribute for storing the node's word order index,
    but assigning to it should be done with care, so the non-root nodes have `ord`s 1,2,3...
    It is recommended to use one of the `node.shift_*` methods for reordering nodes.

    For changing dependency structure (topology) of the tree, there is the `parent` property,
    e.g. `node.parent = node.parent.parent` and `node.create_child()` method.
    Properties `node.children` and `node.descendants` return object of type `ListOfNodes`,
    so it is possible to do e.g.
    >>> all_children = node.children
    >>> left_children = node.children(preceding_only=True)
    >>> right_descendants = node.descendants(following_only=True, add_self=True)

    Properties `node.feats` and `node.misc` return objects of type `DualDict`, so one can do e.g.:
    >>> node = Node()
    >>> str(node.feats)
    '_'
    >>> node.feats = {'Case': 'Nom', 'Person': '1'}`
    >>> node.feats = 'Case=Nom|Person=1' # equivalent to the above
    >>> node.feats['Case']
    'Nom'
    >>> node.feats['NonExistent']
    ''
    >>> node.feats['Case'] = 'Gen'
    >>> str(node.feats)
    'Case=Gen|Person=1'
    >>> dict(node.feats)
    {'Case': 'Gen', 'Person': '1'}

    Handling of enhanced dependencies, multi-word tokens and other node's methods
    are described below.
    """

    # TODO: Benchmark memory and speed of slots vs. classic dict.
    # With Python 3.5 split dict, slots may not be better.
    # TODO: Should not we include __weakref__ in slots?
    __slots__ = [
        'ord',        # Word-order index of the node (root has 0).
        'form',       # Word form or punctuation symbol.
        'lemma',      # Lemma of word form.
        'upos',       # Universal PoS tag.
        'xpos',       # Language-specific part-of-speech tag; underscore if not available.
        'deprel',     # UD dependency relation to the HEAD (root iff HEAD = 0).
        '_misc',      # Any other annotation as udapi.core.dualdict.DualDict object.
        '_raw_deps',  # Enhanced dependencies (head-deprel pairs) in their original CoNLLU format.
        '_deps',      # Deserialized enhanced dependencies in a list of {parent, deprel} dicts.
        '_feats',     # Morphological features as udapi.core.feats.Feats object.
        '_parent',    # Parent node.
        '_children',  # Ord-ordered list of child nodes.
        '_mwt',       # Multi-word token in which this word participates.
    ]

    def __init__(self, form=None, lemma=None, upos=None,  # pylint: disable=too-many-arguments
                 xpos=None, feats=None, deprel=None, misc=None):
        """Create a new node and initialize its attributes using the keyword arguments."""
        self.ord = None
        self.form = form
        self.lemma = lemma
        self.upos = upos
        self.xpos = xpos
        self._feats = Feats(feats)
        self.deprel = deprel
        self._misc = DualDict(misc)
        self._raw_deps = '_'
        self._deps = None
        self._parent = None
        self._children = list()
        self._mwt = None

    def __str__(self):
        """Pretty print of the Node object."""
        return "node<%s, %s>" % (self.address(), self.form)

    @property
    def udeprel(self):
        """Return the universal part of dependency relation, e.g. `acl` instead of `acl:relcl`.

        So you can write `node.udeprel` instead of `node.deprel.split(':')[0]`.
        """
        return self.deprel.split(':')[0] if self.deprel is not None else None

    @udeprel.setter
    def udeprel(self, value):
        sdeprel = self.sdeprel
        if sdeprel is not None and sdeprel != '':
            self.deprel = value + ':' + sdeprel
        else:
            self.deprel = value

    @property
    def sdeprel(self):
        """Return the language-specific part of dependency relation.

        E.g. if deprel = `acl:relcl` then sdeprel = `relcl`.
        If deprel=`acl` then sdeprel = empty string.
        If deprel is `None` then `node.sdeprel` will return `None` as well.
        """
        if self.deprel is None:
            return None
        parts = self.deprel.split(':', 1)
        if len(parts) == 2:
            return parts[1]
        return ''

    @property
    def feats(self):
        """Property for morphological features stored as a `Feats` object.

        Reading:
        You can access `node.feats` as a dict, e.g. `if node.feats['Case'] == 'Nom'`.
        Features which are not set return an empty string (not None, not KeyError),
        so you can safely use e.g. `if node.feats['MyExtra'].find('substring') != -1`.
        You can also obtain the string representation of the whole FEATS (suitable for CoNLL-U),
        e.g. `if node.feats == 'Case=Nom|Person=1'`.

        Writing:
        All the following assignment types are supported:
        `node.feats['Case'] = 'Nom'`
        `node.feats = {'Case': 'Nom', 'Person': '1'}`
        `node.feats = 'Case=Nom|Person=1'`
        `node.feats = '_'`
        The last line has the same result as assigning None or empty string to `node.feats`.

        For details about the implementation and other methods (e.g. `node.feats.is_plural()`),
        see ``udapi.core.feats.Feats`` which is a subclass of `DualDict`.
        """
        return self._feats

    @feats.setter
    def feats(self, value):
        self._feats.set_mapping(value)

    @property
    def misc(self):
        """Property for MISC attributes stored as a `DualDict` object.

        Reading:
        You can access `node.misc` as a dict, e.g. `if node.misc['SpaceAfter'] == 'No'`.
        Features which are not set return an empty string (not None, not KeyError),
        so you can safely use e.g. `if node.misc['MyExtra'].find('substring') != -1`.
        You can also obtain the string representation of the whole MISC (suitable for CoNLL-U),
        e.g. `if node.misc == 'SpaceAfter=No|X=Y'`.

        Writing:
        All the following assignment types are supported:
        `node.misc['SpaceAfter'] = 'No'`
        `node.misc = {'SpaceAfter': 'No', 'X': 'Y'}`
        `node.misc = 'SpaceAfter=No|X=Y'`
        `node.misc = '_'`
        The last line has the same result as assigning None or empty string to `node.feats`.

        For details about the implementation, see ``udapi.core.dualdict.DualDict``.
        """
        return self._misc

    @misc.setter
    def misc(self, value):
        self._misc.set_mapping(value)

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
            self._raw_deps = '|'.join(serialized_deps)
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
            raise ValueError('Cannot set a node as its own parent (cycle are forbidden): %s' % self)

        # Check if the current Node is not an antecedent of the new parent.
        climbing_node = new_parent
        while not climbing_node.is_root():
            if climbing_node == self:
                raise ValueError('Setting the parent of %s to %s would lead to a cycle.'
                                 % (self, new_parent))
            climbing_node = climbing_node.parent

        # Remove the current Node from the children of the old parent.
        # Forbid moving nodes from one tree to another using parent setter.
        if self._parent:
            self._parent._children = [node for node in self.parent.children if node != self]
            # TODO: .root is currently computed, so it is quite slow
            old_root, new_root = self._parent.root, climbing_node
            if old_root != new_root:
                raise ValueError('Cannot move nodes between trees with parent setter, '
                                 'use new_root.steal_nodes(nodes_to_be_moved) instead')
        # Set the new parent.
        self._parent = new_parent

        # Append the current node to the new parent children.
        new_parent._children = sorted(new_parent.children + [self], key=lambda child: child.ord)

    @property
    def children(self):
        """Return a list of dependency children (direct dependants) nodes.

        The returned nodes are sorted by their ord.
        Note that node.children is a property, not a method,
        so if you want all the children of a node (excluding the node itself),
        you should not use node.children(), but just
         node.children
        However, the returned result is a callable list, so you can use
         nodes1 = node.children(add_self=True)
         nodes2 = node.children(following_only=True)
         nodes3 = node.children(preceding_only=True)
         nodes4 = node.children(preceding_only=True, add_self=True)
        as a shortcut for
         nodes1 = sorted([node] + node.children, key=lambda n: n.ord)
         nodes2 = [n for n in node.children if n.ord > node.ord]
         nodes3 = [n for n in node.children if n.ord < node.ord]
         nodes4 = [n for n in node.children if n.ord < node.ord] + [node]
        See documentation of ListOfNodes for details.
        """
        return ListOfNodes(self._children, origin=self)

    @property
    def root(self):
        """Return the (technical) root node of the whole tree."""
        node = self
        while node.parent:
            node = node.parent
        return node

    @property
    def descendants(self):
        """Return a list of all descendants of the current node.

        The returned nodes are sorted by their ord.
        Note that node.descendants is a property, not a method,
        so if you want all the descendants of a node (excluding the node itself),
        you should not use node.descendants(), but just
         node.descendants
        However, the returned result is a callable list, so you can use
         nodes1 = node.descendants(add_self=True)
         nodes2 = node.descendants(following_only=True)
         nodes3 = node.descendants(preceding_only=True)
         nodes4 = node.descendants(preceding_only=True, add_self=True)
        as a shortcut for
         nodes1 = sorted([node] + node.descendants, key=lambda n: n.ord)
         nodes2 = [n for n in node.descendants if n.ord > node.ord]
         nodes3 = [n for n in node.descendants if n.ord < node.ord]
         nodes4 = [n for n in node.descendants if n.ord < node.ord] + [node]
        See documentation of ListOfNodes for details.
        """
        return ListOfNodes(sorted(self.unordered_descendants(), key=lambda n: n.ord), origin=self)

    def is_descendant_of(self, node):
        """Is the current node a descendant of the node given as argument?"""
        climber = self.parent
        while climber:
            if climber == node:
                return True
            climber = climber.parent
        return False

    def create_child(self, **kwargs):
        """Create and return a new child of the current node."""
        new_node = Node(**kwargs)
        new_node.ord = len(self.root._descendants) + 1
        self.root._descendants.append(new_node)
        self.children.append(new_node)
        new_node.parent = self
        return new_node

    def create_empty_child(self, **kwargs):
        """Create and return a new empty node child of the current node."""
        new_node = Node(**kwargs)
        self.root.empty_nodes.append(new_node)
        # self.enh_children.append(new_node) TODO
        # new_node.enh_parents.append(self) TODO
        return new_node

    # TODO: make private: _unordered_descendants
    def unordered_descendants(self):
        """Return a list of all descendants in any order."""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.unordered_descendants())
        return descendants

    @staticmethod
    def is_root():
        """Is the current node a (technical) root?

        Returns False for all Node instances, irrespectively of whether is has a parent or not.
        True is returned only by instances of udapi.core.root.Root.
        """
        return False

    def remove(self, children=None):
        """Delete this node and all its descendants.

        Args:
        children: a string specifying what to do if the node has any children.
            The default (None) is to delete them (and all their descendants).
            `rehang` means to re-attach those children to the parent of the removed node.
            `warn` means to issue a warning if any children are present and delete them.
            `rehang_warn` means to rehang and warn:-).
        """
        self.parent._children = [child for child in self.parent.children if child != self]
        if children is not None and self.children:
            if children.startswith('rehang'):
                for child in self.children:
                    child.parent = self.parent
            if children.endswith('warn'):
                logging.warning('%s is being removed by remove(children=%s), '
                                ' but it has (unexpected) children', self, children)
        self.root._update_ordering()

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

        self.root._update_ordering()

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

    @property
    def prev_node(self):
        """Return the previous node according to word order."""
        new_ord = self.ord - 1
        if new_ord < 0:
            return None
        if new_ord == 0:
            return self.root
        return self.root._descendants[new_ord - 1]

    @property
    def next_node(self):
        """Return the following node according to word order."""
        # Note that all_nodes[n].ord == n+1
        try:
            return self.root._descendants[self.ord]
        except IndexError:
            return None

    def precedes(self, node):
        """Does this node precedes another `node` in word order (`self.ord < node.ord`)?"""
        return self.ord < node.ord

    def is_leaf(self):
        """Is this node a leaf, ie. a node without any children?"""
        return not self.children

    def _get_attr(self, name):  # pylint: disable=too-many-return-statements
        if name == 'dir':
            if self.parent.is_root():
                return 'root'
            return 'left' if self.precedes(self.parent) else 'right'
        if name == 'edge':
            if self.parent.is_root():
                return 0
            return self.ord - self.parent.ord
        if name == 'children':
            return len(self.children)
        if name == 'siblings':
            return len(self.parent.children) - 1
        if name == 'depth':
            value = 0
            tmp = self
            while not tmp.is_root():
                tmp = tmp.parent
                value += 1
            return value
        if name == 'feats_split':
            return str(self.feats).split('|')
        return getattr(self, name)

    def get_attrs(self, attrs, undefs=None, stringify=True):
        """Return multiple attributes or pseudo-attributes, possibly substituting empty ones.

        Pseudo-attributes:
        p_xy is the (pseudo) attribute xy of the parent node.
        c_xy is a list of the (pseudo) attributes xy of the children nodes.
        l_xy is the (pseudo) attribute xy of the previous (left in LTR langs) node.
        r_xy is the (pseudo) attribute xy of the following (right in LTR langs) node.
        dir: 'left' = the node is a left child of its parent,
             'right' = the node is a rigth child of its parent,
             'root' = the node's parent is the technical root.
        edge: length of the edge to parent (`node.ord - node.parent.ord`) or 0 if parent is root
        children: number of children nodes.
        siblings: number of siblings nodes.
        depth: depth in the dependency tree (technical root has depth=0, highest word has depth=1).
        feats_split: list of name=value formatted strings of the FEATS.

        Args:
        attrs: A list of attribute names, e.g. ``['form', 'lemma', 'p_upos']``.
        undefs: A value to be used instead of None for empty (undefined) values.
        stringify: Apply `str()` on each value (except for None)
        """
        values = []
        for name in attrs:
            nodes = [self]
            if name.startswith('p_'):
                nodes, name = [self.parent], name[2:]
            elif name.startswith('c_'):
                nodes, name = self.children, name[2:]
            elif name.startswith('l_'):
                nodes, name = [self.prev_node], name[2:]
            elif name.startswith('r_'):
                nodes, name = [self.next_node], name[2:]
            for node in (n for n in nodes if n is not None):
                if name == 'feats_split':
                    values.extend(node._get_attr(name))
                else:
                    values.append(node._get_attr(name))

        if undefs is not None:
            values = [x if x is not None else undefs for x in values]
        if stringify:
            values = [str(x) if x is not None else None for x in values]
        return values

    def compute_text(self, use_mwt=True):
        """Return a string representing this subtree's text (detokenized).

        Compute the string by concatenating forms of nodes
        (words and multi-word tokens) and joining them with a single space,
        unless the node has SpaceAfter=No in its misc.
        If called on root this method returns a string suitable for storing
        in root.text (but it is not stored there automatically).

        Technical details:
        If called on root, the root's form (<ROOT>) is not included in the string.
        If called on non-root nodeA, nodeA's form is included in the string,
        i.e. internally descendants(add_self=True) is used.
        Note that if the subtree is non-projective, the resulting string may be misleading.

        Args:
        use_mwt: consider multi-word tokens? (default=True)
        """
        string = ''
        last_mwt_id = 0
        for node in self.descendants(add_self=not self.is_root()):
            mwt = node.multiword_token
            if use_mwt and mwt:
                if node.ord > last_mwt_id:
                    last_mwt_id = mwt.words[-1].ord
                    string += mwt.form
                    if mwt.misc['SpaceAfter'] != 'No':
                        string += ' '
            else:
                string += node.form
                if node.misc['SpaceAfter'] != 'No':
                    string += ' '
        return string.rstrip()

    def print_subtree(self, **kwargs):
        """Print ASCII visualization of the dependency structure of this subtree.

        This method is useful for debugging.
        Internally udapi.block.write.textmodetrees.TextModeTrees is used for the printing.
        All keyword arguments of this method are passed to its constructor,
        so you can use e.g.:
        files: to redirect sys.stdout to a file
        indent: to have wider trees
        attributes: to override the default list 'form,upos,deprel'
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
        return '%s#%d' % (self.root.address() if self.root else '?', self.ord)

    @property
    def multiword_token(self):
        """Return the multi-word token which includes this node, or None.

        If this node represents a (syntactic) word which is part of a multi-word token,
        this method returns the instance of udapi.core.mwt.MWT.
        If this nodes is not part of any multi-word token, this method returns None.
        """
        return self._mwt

    def is_nonprojective(self):
        """Is the node attached to its parent non-projectively?

        Is there at least one node between (word-order-wise) this node and its parent
        that is not dominated by the parent?
        For higher speed, the actual implementation does not find the node(s)
        which cause(s) the gap. It only checks the number of parent's descendants in the span
        and the total number of nodes in the span.
        """
        # Root and its children are always projective
        parent = self.parent
        if not parent or parent.is_root():
            return False

        # Edges between neighboring nodes are always projective.
        # Check it now to make it a bit faster.
        ord1, ord2 = self.ord, parent.ord
        if ord1 > ord2:
            ord1, ord2 = ord2, ord1
        distance = ord2 - ord1
        if distance == 1:
            return False

        # Get all the descendants of parent that are in the span of the edge.
        span = [n for n in parent.descendants if n.ord > ord1 and n.ord < ord2]

        # For projective edges, span must include all the nodes between parent and self.
        return len(span) != distance - 1

    def is_nonprojective_gap(self):
        """Is the node causing a non-projective gap within another node's subtree?

        Is there at least one node X such that
        - this node is not a descendant of X, but
        - this node is within span of X, i.e. it is between (word-order-wise)
          X's leftmost descendant (or X itself) and X's rightmost descendant (or X itself).
        """
        ancestors = set()
        node = self
        while node.parent:
            ancestors.add(node)
            node = node.parent
        all_nodes = node.descendants
        for left_node in all_nodes[:self.ord - 1]:
            if self.precedes(left_node.parent) and left_node.parent not in ancestors:
                return True
        for right_node in all_nodes[self.ord:]:
            if right_node.parent.precedes(node) and right_node.parent not in ancestors:
                return True
        return False

    @property
    def no_space_after(self):
        """Boolean property as a shortcut for `node.misc["SpaceAfter"] == "No"`."""
        return self.misc["SpaceAfter"] == "No"


class ListOfNodes(list):
    """Helper class for results of node.children and node.descendants.

    Python distinguishes properties, e.g. node.form ... no brackets,
    and methods, e.g. node.remove() ... brackets necessary.
    It is useful (and expected by Udapi users) to use properties,
    so one can do e.g. node.form += "suffix".
    It is questionable whether node.parent, node.root, node.children etc.
    should be properties or methods. The problem of methods is that
    if users forget the brackets, the error may remain unnoticed
    because the result is interpreted as a method reference.
    The problem of properties is that they cannot have any parameters.
    However, we would like to allow e.g. node.children(add_self=True).

    This class solves the problem: node.children and node.descendants
    are properties which return instances of this clas ListOfNodes.
    This class implements the method __call__, so one can use e.g.
    nodes = node.children
    nodes = node.children()
    nodes = node.children(add_self=True, following_only=True)
    """

    def __init__(self, iterable, origin):
        """Create a new ListOfNodes.

        Args:
        iterable: a list of nodes
        origin: a node which is the parent/ancestor of these nodes
        """
        super().__init__(iterable)
        self.origin = origin

    def __call__(self, add_self=False, following_only=False, preceding_only=False):
        """Returns a subset of nodes contained in this list as specified by the args."""
        if not add_self and not following_only and not preceding_only:
            return self
        result = list(self)
        if add_self:
            result.append(self.origin)
        if preceding_only:
            result = [x for x in result if x.ord <= self.origin.ord]
        if following_only:
            result = [x for x in result if x.ord >= self.origin.ord]
        return sorted(result, key=lambda node: node.ord)


def find_minimal_common_treelet(*args):
    """Find the smallest tree subgraph containing all `nodes` provided in args.

    >>> from udapi.core.node import find_minimal_common_treelet
    >>> (nearest_common_ancestor, _) = find_minimal_common_treelet(nodeA, nodeB)
    >>> nodes = [nodeA, nodeB, nodeC]
    >>> (nca, added_nodes) = find_minimal_common_treelet(*nodes)

    There always exists exactly one such tree subgraph (aka treelet).
    This function returns a tuple `(root, added_nodes)`,
    where `root` is the root of the minimal treelet
    and `added_nodes` is an iterator of nodes that had to be added to `nodes` to form the treelet.
    The `nodes` should not contain one node twice.
    """
    nodes = list(args)
    # The input nodes are surely in the treelet, let's mark this with "1".
    in_treelet = {node.ord: 1 for node in nodes}

    # Step 1: Find a node (`highest`) which is governing all the input `nodes`.
    #         It may not be the lowest such node, however.
    # At the beginning, each node in `nodes` represents (a top node of) a "component".
    # We climb up from all `nodes` towards the root "in parallel".
    # If we encounter an already visited node, we mark the node (`in_treelet[node.ord] = 1`)
    # as a "sure" member of the treelet and we merge the two components,
    # i.e. we delete this second component from `nodes`,
    # in practice we just skip the command `nodes.append(parent)`.
    # Otherwise, we mark the node as "unsure".
    # For unsure members we need to mark from which of its children
    # we climbed to it (`in_treelet[paren.ord] = the_child`).
    # In `new_nodes` dict, we note which nodes were tentatively added to the treelet.
    # If we climb up to the root of the whole tree, we save the root in `highest`.
    new_nodes = {}
    highest = None
    while len(nodes) > 1:
        node = nodes.pop(0)  # TODO deque
        parent = node.parent
        if parent is None:
            highest = node
        elif in_treelet.get(parent.ord, False):
            in_treelet[parent.ord] = 1
        else:
            new_nodes[parent.ord] = parent
            in_treelet[parent.ord] = node
            nodes.append(parent)

    # In most cases, `nodes` now contain just one node -- the one we were looking for.
    # Only if we climbed up to the root, then the `highest` one is the root, of course.
    highest = highest or nodes[0]

    # Step 2: Find the lowest node which is governing all the original input `nodes`.
    # If the `highest` node is unsure, climb down using poiners stored in `in_treelet`.
    # All such nodes which were rejected as true members of the minimal common treelet
    # must be deleted from the set of newly added nodes `new_nodes`.
    child = in_treelet[highest.ord]
    while child != 1:
        del new_nodes[highest.ord]
        highest = child
        child = in_treelet[highest.ord]

    # We return the root of the minimal common treelet plus all the newly added nodes.
    return (highest, new_nodes.values())
