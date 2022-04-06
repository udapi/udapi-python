"""Node class and related classes and functions.

In addition to class `Node`, this module contains also helper classes
`CycleError`, `EmptyNode`, `OrdTuple` and `ListOfNodes`
and function `find_minimal_common_treelet`.
"""
import logging
import functools

import udapi.core.coref
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

@functools.total_ordering
class Node(object):
    """Class for representing nodes in Universal Dependency trees.

    Attributes `form`, `lemma`, `upos`, `xpos` and `deprel` are public attributes of type `str`,
    so you can use e.g. `node.lemma = node.form`.

    `node.ord` is a int type property for storing the node's word-order index,
    but assigning to it should be done with care, so the non-root nodes have `ord`s 1,2,3...
    It is recommended to use one of the `node.shift_*` methods for reordering nodes.
    Note that `EmptyNode`s (subclass of `Node`) have decimal ords (and no `shift_*` methods).

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
    # TODO: Benchmark using node._ord instead node.ord in this file
    __slots__ = [
        '_ord',       # Word-order index of the node (root has 0).
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
        '_root',      # Technical root of the tree
        '_mwt',       # Multi-word token in which this word participates.
        '_mentions',  # List of udapi.core.coref.CorefMention objects whose span includes this node
    ]

    def __init__(self, root, form=None, lemma=None, upos=None,  # pylint: disable=too-many-arguments
                 xpos=None, feats=None, deprel=None, misc=None):
        """Create a new node and initialize its attributes using the keyword arguments."""
        self._root = root
        self._ord = None
        self.form = form
        self.lemma = lemma
        self.upos = upos
        self.xpos = xpos
        self._feats = Feats(feats) if feats and feats != '_' else None
        self.deprel = deprel
        self._misc = DualDict(misc) if misc and misc != '_' else None
        self._raw_deps = '_'
        self._deps = None
        self._parent = None
        self._children = list()
        self._mwt = None
        self._mentions = list()

    def __str__(self):
        """String representation of the Node object: <n.address(), n.form>."""
        return f"<{self.address()}, {self.form}>"

    def __repr__(self):
        """String representation of the Node object: Node<n.address(), n.form>."""
        return f"Node<{self.address()}, {self.form}>"


    @property
    def root(self):
        return self._root

    # ord is implemented as a property, so that it can be overriden in EmptyNode and Root
    @property
    def ord(self):
        return self._ord

    @ord.setter
    def ord(self, new_ord):
        self._ord = new_ord

    def __lt__(self, other):
        """Calling `nodeA < nodeB` is equivalent to `nodeA.ord < nodeB.ord`.

        Note that this does not work as expected for nodes from different trees
        because `ord` is the word order within each sentence.
        For comparing the word order across trees, use `nodeA.precedes(nodeB)` instead.
        """
        return self._ord < other._ord

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
        if self._feats is None:
            self._feats = Feats()
        return self._feats

    @feats.setter
    def feats(self, value):
        if self._feats is None:
            self._feats = Feats(value)
        else:
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
    def raw_deps(self):
        """String serialization of enhanced dependencies as stored in CoNLL-U files.

        After the access to the raw enhanced dependencies,
        provide the serialization if they were deserialized already.
        """
        # TODO: node.deps.append(dep) should be hooked and
        # mark the serialized cache dirty, i.e. self._raw_deps = None.
        # Afterwards, we can use the following optimization
        #if self._raw_deps is not None:
        #    return self._raw_deps
        if self._deps:
            self._raw_deps = '|'.join(f"{dep['parent']._ord}:{dep['deprel']}" for dep in self._deps)
        return self._raw_deps

    @raw_deps.setter
    def raw_deps(self, value):
        """Set serialized enhanced dependencies (the new value is a string).

        When updating raw secondary dependencies,
        the current version of the deserialized data is deleted.
        """
        self._raw_deps = value
        self._deps = None

    @property
    def deps(self):
        """Return enhanced dependencies as a Python list of dicts.

        After the first access to the enhanced dependencies,
        provide the deserialization of the raw data and save deps to the list.
        """
        if self._deps is None:
            # Create a list of secondary dependencies.
            self._deps = list()

            if self._raw_deps == '_':
                return self._deps

            # Obtain a list of all nodes in the dependency tree.
            nodes = [self._root] + self._root._descendants

            for raw_dependency in self._raw_deps.split('|'):
                # Deprel itself may contain one or more ':' (subtypes).
                head, deprel = raw_dependency.split(':', maxsplit=1)
                # Empty nodes have to be located differently than normal nodes.
                if '.' in head:
                    try:
                        parent = next(x for x in self._root.empty_nodes if str(x._ord) == head)
                    except StopIteration:
                        raise ValueError(f'Empty node with ord={head} not found')
                else:
                    parent = nodes[int(head)]
                self._deps.append({'parent': parent, 'deprel': deprel})

        return self._deps

    @deps.setter
    def deps(self, value):
        """Set deserialized enhanced dependencies (the new value is a list of dicts)."""
        self._deps = value
        self._raw_deps = None

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
        if self._parent is new_parent:
            return

        # Check for None new_parent and cycles.
        if new_parent is None:
            raise ValueError(f'Cannot set None as parent: {self}')
        if self is new_parent:
            raise CycleError('Cannot set a node as its own parent (cycle are forbidden): %s', self)
        if self._children and new_parent.is_descendant_of(self):
            raise CycleError('Setting the parent of %s to %s would lead to a cycle.', self, new_parent)

        # Remove the current Node from the children of the old parent.
        # Forbid moving nodes from one tree to another using parent setter.
        if self._parent:
            self._parent._children.remove(self)
            if self._parent._root is not new_parent._root:
                raise ValueError('Cannot move nodes between trees with parent setter, '
                                 'use new_root.steal_nodes(nodes_to_be_moved) instead')
        # Set the new parent.
        self._parent = new_parent

        # Append the current node to the new parent children.
        if not new_parent._children or self > new_parent._children[-1]:
            new_parent._children.append(self)
        else:
            new_parent._children.append(self)
            new_parent._children.sort()

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
        See the documentation of ListOfNodes for details.
        """
        return ListOfNodes(self._children, origin=self)

    @property
    def siblings(self):
        """Return a list of dependency sibling nodes.

        When used as a property, `node.siblings` is just a shortcut for:
         [n for n in node.parent.children if n!=node]
        However, it is especially helpful when used as a method,
        so e.g. `node.siblings(preceding_only=True)` stands for
         [n for n in node.parent.children if n.ord < node.ord]
        which is something else than
         node.parent.children(preceding_only=True).
        See the documentation of ListOfNodes for details.
        """
        return ListOfNodes([n for n in self._parent._children if n!=self], origin=self)

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
        See the documentation of ListOfNodes for details.
        """
        # The following code is equivalent to
        # ListOfNodes(sorted(self.unordered_descendants()), origin=self)
        # but it is faster because there is no extra copying of lists of nodes.
        stack = list(self._children)
        descendants = ListOfNodes(stack, origin=self)
        while(stack):
            n = stack.pop()
            if n._children:
                stack.extend(n._children)
                descendants.extend(n._children)
        descendants.sort()
        return descendants

    def is_descendant_of(self, node):
        """Is the current node a descendant of the node given as argument?"""
        if node and node._children:
            climber = self._parent
            while climber:
                if climber is node:
                    return True
                climber = climber._parent
        return False

    def create_child(self, **kwargs):
        """Create and return a new child of the current node."""
        new_node = Node(root=self._root, **kwargs)
        new_node._ord = len(self._root._descendants) + 1
        self._root._descendants.append(new_node)
        self._children.append(new_node)
        new_node._parent = self
        return new_node

    def create_empty_child(self, deprel, after=True, **kwargs):
        """Create and return a new empty node child of the current node.

        Args:
            deprel: the enhanced dependency relation (required to be stored in DEPS)
            form, lemma, upos, xpos, feats, misc: as in Node, the default is '_'
            after: position the newly created empty node after this `node`?
                If True (default), the `new_node.ord` will be `node.ord + 0.1`,
                unless there is already an empty node with such ord,
                in which case it will be `node.ord + 0.2` etc.
                If False, the new node will be placed immediately before `node`.
        """
        new_node = EmptyNode(root=self._root, **kwargs)
        new_node.deps = [{'parent': self, 'deprel': deprel}]
        # self.enh_children.append(new_node) TODO
        # new_node.enh_parents.append(self) TODO
        base_ord = self._ord if after else self._ord - 1
        new_ord = base_ord + 0.1
        for empty in self._root.empty_nodes:
            if empty._ord > new_ord:
                break
            if empty._ord == new_ord:
                if isinstance(new_ord, OrdTuple):
                    new_ord.increase()
                elif new_ord == base_ord + 0.9:
                    new_ord = OrdTuple(base_ord, 10)
                else:
                    new_ord = round(new_ord+0.1, 1)
        new_node._ord = new_ord
        if not self._root.empty_nodes or new_node > self._root.empty_nodes[-1]:
            self._root.empty_nodes.append(new_node)
        else:
            self._root.empty_nodes.append(new_node)
            self._root.empty_nodes.sort()
        return new_node

    # TODO: make private: _unordered_descendants
    def unordered_descendants(self):
        """Return a list of all descendants in any order."""
        stack = list(self._children)
        descendants = list(stack)
        while(stack):
            n = stack.pop()
            if n._children:
                stack.extend(n._children)
                descendants.extend(n._children)
        return descendants

    @staticmethod
    def is_root():
        """Is the current node a (technical) root?

        Returns False for all Node instances, irrespectively of whether is has a parent or not.
        True is returned only by instances of udapi.core.root.Root.
        """
        return False

    @staticmethod
    def is_empty():
        """Is the current node an empty node?

        Returns False for all Node instances.
        True is returned only by instances of the EmptyNode subclass.
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
        self._parent._children.remove(self)
        if children is not None and self._children:
            if children.startswith('rehang'):
                for child in self._children:
                    child._parent = self._parent
                self._parent._children.extend(self._children)
                self._parent._children.sort()
                self._children.clear()
            if children.endswith('warn'):
                logging.warning('%s is being removed by remove(children=%s), '
                                ' but it has (unexpected) children', self, children)

        # When self is the only node being removed, it is faster to root._descendants.remove(self)
        # and update the ords only where necessary (from self._ord further).
        # When removing also its children+descendants, it is faster to recompute root._descendants
        # and update all ords (computing leftmost descendant of self would be too slow).
        if not self._children:
            try:
                self._root._descendants.remove(self)
            except ValueError:
                pass # self may be an already deleted node e.g. if n.remove() called twice
            for (new_ord, node) in enumerate(self._root._descendants[self._ord - 1:], self._ord):
                node.ord = new_ord
        else:
            # TODO nodes_to_remove = self.unordered_descendants()
            # and mark all nodes as deleted, remove them from MWT and coref mentions
            self._root._descendants = sorted(self._root.unordered_descendants())
            for (new_ord, node) in enumerate(self._root._descendants, 1):
                node.ord = new_ord

    def _shift_before_ord(self, reference_ord, without_children=False):
        """Internal method for changing word order."""
        all_nodes = self._root._descendants

        # Moving a single node can be faster than nodes_to_move = [self]
        if without_children or not self._children:
            my_ord = self._ord
            if reference_ord > my_ord + 1:
                for i_ord in range(my_ord, reference_ord - 1):
                    all_nodes[i_ord - 1] = all_nodes[i_ord]
                    all_nodes[i_ord - 1]._ord = i_ord
                all_nodes[reference_ord - 2] = self
                self._ord = reference_ord - 1
            elif reference_ord < my_ord:
                for i_ord in range(my_ord, reference_ord, -1):
                    all_nodes[i_ord - 1] = all_nodes[i_ord - 2]
                    all_nodes[i_ord - 1]._ord = i_ord
                all_nodes[reference_ord - 1] = self
                self._ord = reference_ord
            return

        nodes_to_move = self.descendants(add_self=True)
        first_ord, last_ord = nodes_to_move[0]._ord, nodes_to_move[-1]._ord

        # If there are no "gaps" in nodes_to_move (e.g. when it is projective),
        # we can make the shifting a bit faster and simpler.
        if last_ord - first_ord + 1 == len(nodes_to_move):
            # First, move a node from position src_ord to position trg_ord RIGHT-ward.
            trg_ord, src_ord = last_ord, first_ord - 1
            while src_ord >= reference_ord:
                all_nodes[trg_ord - 1] = all_nodes[src_ord - 1]
                all_nodes[trg_ord-1]._ord = trg_ord
                trg_ord, src_ord = trg_ord - 1, src_ord - 1
            # Second, move a node from position src_ord to position trg_ord LEFT-ward.
            trg_ord, src_ord = first_ord, last_ord + 1
            while src_ord < reference_ord:
                all_nodes[trg_ord - 1] = all_nodes[src_ord - 1]
                all_nodes[trg_ord - 1]._ord = trg_ord
                trg_ord, src_ord = trg_ord + 1, src_ord + 1
            # Third, move nodes_to_move to trg_ord RIGHT-ward.
            trg_ord = reference_ord if reference_ord < first_ord else trg_ord
            for node in nodes_to_move:
                all_nodes[trg_ord - 1], node._ord = node, trg_ord
                trg_ord += 1
            return

        # First, move a node from position src_ord to position trg_ord RIGHT-ward.
        # src_ord iterates decreasingly over nodes which are not moving.
        trg_ord, src_ord, mov_ord = last_ord, last_ord - 1, len(nodes_to_move) - 2
        while src_ord >= reference_ord:
            while all_nodes[src_ord - 1] is nodes_to_move[mov_ord]:
                mov_ord, src_ord = mov_ord - 1, src_ord - 1
                if src_ord < reference_ord:
                    break
            else:
                all_nodes[trg_ord - 1] = all_nodes[src_ord - 1]
                all_nodes[trg_ord - 1]._ord = trg_ord
                trg_ord, src_ord = trg_ord - 1, src_ord - 1

        # Second, move a node from position src_ord to position trg_ord LEFT-ward.
        # src_ord iterates increasingly over nodes which are not moving.
        trg_ord, src_ord, mov_ord = first_ord, first_ord + 1, 1
        while src_ord < reference_ord:
            while mov_ord < len(nodes_to_move) and all_nodes[src_ord - 1] is nodes_to_move[mov_ord]:
                mov_ord, src_ord = mov_ord + 1, src_ord + 1
                if src_ord >= reference_ord:
                    break
            else:
                all_nodes[trg_ord - 1] = all_nodes[src_ord - 1]
                all_nodes[trg_ord - 1]._ord = trg_ord
                trg_ord, src_ord = trg_ord + 1, src_ord + 1

        # Third, move nodes_to_move to trg_ord RIGHT-ward.
        trg_ord = reference_ord if reference_ord < first_ord else trg_ord
        for node in nodes_to_move:
            all_nodes[trg_ord - 1], node._ord = node, trg_ord
            trg_ord += 1

    def shift_after_node(self, reference_node, without_children=False, skip_if_descendant=False):
        """Shift this node after the reference_node."""
        if not without_children and reference_node.is_descendant_of(self):
            if skip_if_descendant:
                return
            raise ValueError(f'{reference_node} is a descendant of {self}. Consider without_children=1.')
        self._shift_before_ord(reference_node._ord + 1, without_children=without_children)

    def shift_before_node(self, reference_node, without_children=False, skip_if_descendant=False):
        """Shift this node after the reference_node."""
        if not without_children and reference_node.is_descendant_of(self):
            if skip_if_descendant:
                return
            raise ValueError(f'{reference_node} is a descendant of {self}. Consider without_children=1.')
        self._shift_before_ord(reference_node._ord, without_children=without_children)

    def shift_after_subtree(self, reference_node, without_children=False, skip_if_descendant=False):
        """Shift this node (and its subtree) after the subtree rooted by reference_node.

        Args:
        without_children: shift just this node without its subtree?
        """
        if not without_children and reference_node.is_descendant_of(self):
            if skip_if_descendant:
                return
            raise ValueError(f'{reference_node} is a descendant of {self}. Consider without_children=1.')
        ref_ord = reference_node._ord
        for node in reference_node.unordered_descendants():
            if node._ord > ref_ord and node is not self:
                ref_ord = node._ord
        self._shift_before_ord(ref_ord + 1, without_children=without_children)

    def shift_before_subtree(self, reference_node, without_children=0, skip_if_descendant=False):
        """Shift this node (and its subtree) before the subtree rooted by reference_node.

        Args:
        without_children: shift just this node without its subtree?
        """
        if not without_children and reference_node.is_descendant_of(self):
            if skip_if_descendant:
                return
            raise ValueError(f'{reference_node} is a descendant of {self}. Consider without_children=1.')
        ref_ord = reference_node._ord
        for node in reference_node.unordered_descendants():
            if node._ord < ref_ord and node is not self:
                ref_ord = node._ord
        self._shift_before_ord(ref_ord, without_children=without_children)

    @property
    def prev_node(self):
        """Return the previous node according to word order."""
        new_ord = self._ord - 1
        if new_ord < 0:
            return None
        if new_ord == 0:
            return self._root
        return self._root._descendants[new_ord - 1]

    @property
    def next_node(self):
        """Return the following node according to word order."""
        # Note that all_nodes[n].ord == n+1
        try:
            return self._root._descendants[self._ord]
        except IndexError:
            return None

    def precedes(self, node):
        """Does this node precedes another `node` in word order?

        This method handles correctly also nodes from different trees (but the same zone).
        If you have nodes from the same tree, it is faster and more elegant to use just `nodeA < nodeB`,
        which is equivalent to calling `nodeA.ord < nodeB.ord`.
        For sorting nodes from the same tree, you can use `nodes.sort()` or `sorted(nodes)`.
        """
        if self._root is node._root:
            return self._ord < node._ord
        if self._root._zone != node._root._zone:
            raise ValueError(f"Cannot compare word order across zones: {self} {node}")
        return self._root._bundle.number < node._root._bundle.number

    def is_leaf(self):
        """Is this node a leaf, ie. a node without any children?"""
        return not self._children

    def _get_attr(self, name):  # pylint: disable=too-many-return-statements
        if name == 'dir':
            if self._parent.is_root():
                return 'root'
            return 'left' if self.precedes(self._parent) else 'right'
        if name == 'edge':
            if self._parent.is_root():
                return 0
            return self._ord - self._parent._ord
        if name == 'children':
            return len(self._children)
        if name == 'siblings':
            return len(self._parent._children) - 1
        if name == 'depth':
            value = 0
            tmp = self
            while not tmp.is_root():
                tmp = tmp._parent
                value += 1
            return value
        if name == 'feats_split':
            return str(self.feats).split('|')
        if name == 'misc_split':
            return str(self.misc).split('|')
        if name.startswith('feats['):
            return self.feats[name[6:-1]]
        if name.startswith('misc['):
            return self.misc[name[5:-1]]
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
                nodes, name = [self._parent], name[2:]
            elif name.startswith('c_'):
                nodes, name = self.children, name[2:]
            elif name.startswith('l_'):
                nodes, name = [self.prev_node], name[2:]
            elif name.startswith('r_'):
                nodes, name = [self.next_node], name[2:]
            for node in (n for n in nodes if n is not None):
                if name in {'feats_split', 'misc_split'}:
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
                if node._ord > last_mwt_id:
                    last_mwt_id = mwt.words[-1]._ord
                    string += mwt.form
                    if mwt.misc['SpaceAfter'] != 'No':
                        string += ' '
            else:
                string += node.form
                if node.misc['SpaceAfter'] != 'No':
                    string += ' '
        return string.rstrip()

    def print_subtree(self, **kwargs):
        """deprecated name for draw()"""
        logging.warning("node.print_subtree() is deprecated, use node.draw() instead.")
        TextModeTrees(**kwargs).process_tree(self)

    def draw(self, **kwargs):
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
        return f"{self._root.address() if self._root else '?'}#{self._ord}"

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
        parent = self._parent
        if not parent or parent.is_root():
            return False

        # Edges between neighboring nodes are always projective.
        # Check it now to make it a bit faster.
        ord1, ord2 = self._ord, parent._ord
        if ord1 > ord2:
            ord1, ord2 = ord2, ord1
        distance = ord2 - ord1
        if distance == 1:
            return False

        # Get all the descendants of parent that are in the span of the edge.
        span = [n for n in parent.unordered_descendants() if n._ord > ord1 and n._ord < ord2]

        # For projective edges, span must include all the nodes between parent and self.
        return len(span) != distance - 1

    def is_nonprojective_gap(self):
        """Is the node causing a non-projective gap within another node's subtree?

        Is there at least one node X such that
        - this node is not a descendant of X, but
        - this node is within span of X, i.e. it is between (word-order-wise)
          X's leftmost descendant (or X itself) and X's rightmost descendant (or X itself).
        """
        ancestors = set([self])
        node = self
        while node._parent:
            node = node._parent
            ancestors.add(node)
        all_nodes = node._descendants
        for left_node in all_nodes[:self._ord - 1]:
            if self.precedes(left_node._parent) and left_node._parent not in ancestors:
                return True
        for right_node in all_nodes[self._ord:]:
            if right_node._parent.precedes(self) and right_node._parent not in ancestors:
                return True
        return False

    @property
    def no_space_after(self):
        """Boolean property as a shortcut for `node.misc["SpaceAfter"] == "No"`."""
        return self.misc["SpaceAfter"] == "No"

    @property
    def gloss(self):
        """String property as a shortcut for `node.misc["Gloss"]`."""
        return self.misc["Gloss"]

    @gloss.setter
    def gloss(self, new_gloss):
        self.misc["Gloss"] = new_gloss

    @property
    def coref_mentions(self):
        self._root.bundle.document._load_coref()
        return self._mentions

    @property
    def coref_entities(self):
        self._root.bundle.document._load_coref()
        return [m.entity for m in self._mentions if m.entity is not None]

    # TODO: is this method useful?
    def create_coref_entity(self, eid=None, etype=None, **kwargs):
        doc = self._root.bundle.document
        entity = doc.create_coref_entity(eid, etype)
        entity.create_mention(head=self, **kwargs)
        return entity


class CycleError(Exception):
    '''A cycle in the dependency tree detected (or would be created).'''
    def __init__(self, message, node1, node2=None):
        self.message = message
        self.node1 = node1
        self.node2 = node2
        super().__init__(message)

    def __str__(self):
        if self.node2 is None:
            return self.message % self.node1
        return self.message % (self.node1, self.node2)

class EmptyNode(Node):
    """Class for representing empty nodes (for ellipsis in enhanced UD)."""

    def is_empty(self):
        """Return True for all EmptyNode instances."""
        return True

    @property
    def parent(self):
        return None

    @parent.setter
    def parent(self, _):
        """Attempts at setting parent of EmptyNode result in AttributeError exception."""
        raise AttributeError('EmptyNode cannot have a (basic-UD) parent.')

    # The ord getter is the same as in Node, but it must be defined,
    # so that we can override the ord setter.
    @property
    def ord(self):
        return self._ord

    @ord.setter
    def ord(self, new_ord):
        """Empty node's ord setter accepts float and str."""
        if isinstance(new_ord, str):
            self._ord = float(new_ord)
        elif isinstance(new_ord, float):
            self._ord = new_ord
        else:
            raise ValueError('Only str and float are allowed for EmptyNode ord setter,'
                             f' but {type(new_ord)} was given.')

    def shift(self, reference_node, after=0, move_subtree=0, reference_subtree=0):
        """Attempts at changing the word order of EmptyNode result in NotImplemented exception."""
        raise NotImplemented('Empty nodes cannot be re-order using shift* methods yet.')

@functools.total_ordering
class OrdTuple:
    """Class for the rare case of 9+ consecutive empty nodes, i.e. ords x.10, x.11 etc.

    Ord 1.10 cannot be stored as float, which would result in 1.1.
    We thus store it as a tuple (1,10) wrapped in OrdTuple, so that comparisons work,
    e.g.: 1.9 < OrdTuple('1.10') < 2
    """
    __slots__ = ('_key')

    def __init__(self, string):
        m = re.match(r'(\d+)\.(\d+)$', string)
        if not m:
            raise ValueError(f"Ord {string} does not match \\d+.\\d+")
        major, minor = int(m.group(1)), int(m.group(2))
        if minor == 0:
            raise ValueError(f"Ord {string} should be stored as int")
        if minor < 10:
            raise ValueError(f"Ord {string} should be stored as float")
        self._key = (major, minor)

    def __repr__(self):
        return f"{self._key[0]}.{self._key[1]}"

    def __eq__(self, other):
        if isinstance(other, int):
            return False
        elif isinstance(other, float):
            return self._key == (int(other), int(10*other - 10*int(other)))
        elif isinstance(other, OrdTuple):
            return self._key == other._key
        else:
            raise ValueError(f"OrdTuple cannot be compared with {type(other)}")

    def __lt__(self, other):
        if isinstance(other, int):
            return self._key < (other, 0)
        elif isinstance(other, float):
            return self._key < (int(other), int(10*other - 10*int(other)))
        elif isinstance(other, OrdTuple):
            return self._key < other._key
        else:
            raise ValueError(f"OrdTuple cannot be compared with {type(other)}")

    def increase(self):
        """Increment the decimal part of this ord."""
        self._key = (self.key[0], self._key[1]+1)


# Implementation note on ListOfNodes
# We could inherit from collections.abc.Sequence, store the list in self._data
# and implement __getitem__ and __len__ by delegating it to self._data.
# I thought it could be faster because we prevent copying of the list in super().__init__(iterable).
# In practice, it is slower because of the delegation: native list's __getitem__ is C-optimized.
# So let's just inherit from list.
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
    __slots__ = ('origin',)

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
        if add_self:
            self.append(self.origin)
            self.sort()
        if preceding_only:
            return [x for x in self if x._ord <= self.origin._ord]
        if following_only:
            return [x for x in self if x._ord >= self.origin._ord]
        return self


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
    in_treelet = {node._ord: 1 for node in nodes}

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
        parent = node._parent
        if parent is None:
            highest = node
        elif in_treelet.get(parent._ord, False):
            in_treelet[parent._ord] = 1
        else:
            new_nodes[parent._ord] = parent
            in_treelet[parent._ord] = node
            nodes.append(parent)

    # In most cases, `nodes` now contain just one node -- the one we were looking for.
    # Only if we climbed up to the root, then the `highest` one is the root, of course.
    highest = highest or nodes[0]

    # Step 2: Find the lowest node which is governing all the original input `nodes`.
    # If the `highest` node is unsure, climb down using poiners stored in `in_treelet`.
    # All such nodes which were rejected as true members of the minimal common treelet
    # must be deleted from the set of newly added nodes `new_nodes`.
    child = in_treelet[highest._ord]
    while child != 1:
        del new_nodes[highest._ord]
        highest = child
        child = in_treelet[highest._ord]

    # We return the root of the minimal common treelet plus all the newly added nodes.
    return (highest, new_nodes.values())
