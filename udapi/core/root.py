"""Root class represents the technical root node in each tree."""
import logging

from udapi.core.node import Node, EmptyNode, ListOfNodes
from udapi.core.mwt import MWT

# 7 instance attributes is too low (CoNLL-U has 10 columns)
# The set of public attributes/properties and methods of Root was well-thought.
# pylint: disable=too-many-instance-attributes


class Root(Node):
    """Class for representing root nodes (technical roots) in UD trees."""
    __slots__ = ['_sent_id', '_zone', '_bundle', '_descendants', '_mwts',
                 'empty_nodes', 'text', 'comment', 'newpar', 'newdoc', 'json']

    # pylint: disable=too-many-arguments
    def __init__(self, zone=None, comment='', text=None, newpar=None, newdoc=None):
        """Create new root node."""
        # Call constructor of the parent object.
        super().__init__(root=self)

        self.ord = 0
        self.form = '<ROOT>'
        self.lemma = '<ROOT>'
        self.upos = '<ROOT>'
        self.xpos = '<ROOT>'
        self.deprel = '<ROOT>'
        self.comment = comment
        self.text = text
        self.newpar = newpar
        self.newdoc = newdoc
        self.json = {}  # TODO: or None and mask as {} in property reader&writer to save memory?

        self._sent_id = None
        self._zone = zone
        self._bundle = None
        self._descendants = []
        self._mwts = []
        self.empty_nodes = []  # TODO: private

    @property
    def sent_id(self):
        """ID of this tree, stored in the sent_id comment in CoNLL-U."""
        if self._sent_id is not None:
            return self._sent_id
        zone = '/' + self.zone if self.zone else ''
        if self._bundle is not None:
            self._sent_id = self._bundle.address() + zone
        else:
            return '?' + zone
        return self._sent_id

    @sent_id.setter
    def sent_id(self, sent_id):
        if self._bundle is not None:
            parts = sent_id.split('/', 1)
            self._bundle.bundle_id = parts[0]
            if len(parts) == 2:
                self.zone = parts[1]
        self._sent_id = sent_id

    def address(self):
        """Full (document-wide) id of the root.

        The general format of root nodes is:
        root.bundle.bundle_id + '/' + root.zone, e.g. s123/en_udpipe.
        If zone is empty, the slash is excluded as well, e.g. s123.
        If bundle is missing (could occur during loading), '?' is used instead.
        Root's address is stored in CoNLL-U files as sent_id (in a special comment).
        """
        return self.sent_id

    @property
    def document(self):
        return self._bundle._document

    @property
    def bundle(self):
        """Return the bundle which this tree belongs to."""
        return self._bundle

    @bundle.setter
    def bundle(self, bundle):
        self._bundle = bundle

    @property
    def zone(self):
        """Return zone (string label) of this tree."""
        return self._zone

    @zone.setter
    def zone(self, zone):
        """Specify which zone the root belongs to."""
        if self._bundle:
            self._bundle.check_zone(zone)
        self._zone = zone

    @property
    def parent(self):
        """Return dependency parent (head) node.

        This root-specific implementation returns always None.
        """
        return None

    @parent.setter
    def parent(self, _):
        """Attempts at setting parent of root result in AttributeError exception."""
        raise AttributeError('The technical root cannot have a parent.')

    @property
    def descendants(self):
        """Return a list of all descendants of the current node.

        The nodes are sorted by their ord.
        This root-specific implementation returns all the nodes in the tree except the root itself.
        """
        return ListOfNodes(self._descendants, origin=self)

    def is_descendant_of(self, node):
        """Is the current node a descendant of the node given as argument?

        This root-specific implementation returns always False.
        """
        return False

    def is_root(self):
        """Return True for all Root instances."""
        return True

    def remove(self, children=None):
        """Remove the whole tree from its bundle.

        Args:
        children: a string specifying what to do if the root has any children.
            The default (None) is to delete them (and all their descendants).
            `warn` means to issue a warning.
        """
        if children is not None and self.children:
            logging.warning('%s is being removed by remove(children=%s), '
                            ' but it has (unexpected) children', self, children)
        self.bundle.trees = [root for root in self.bundle.trees if root != self]

    def shift(self, reference_node, after=0, move_subtree=0, reference_subtree=0):
        """Attempts at changing the word order of root result in Exception."""
        raise Exception('Technical root cannot be shifted as it is always the first node')

    def create_empty_child(self, **kwargs):
        """Create and return a new empty node within this tree.

        This root-specific implementation overrides `Node.create_empty_child()'.
        It is faster because it does not set `deps` and `ord` of the newly created node.
        It is up to the user to set up these attributes correctly.
        It is used in `udapi.block.read.conllu` (where speed is important and thus,
        only `raw_deps` are set up instead of `deps`).
        """
        new_node = EmptyNode(root=self, **kwargs)
        self.empty_nodes.append(new_node)
        return new_node

    # TODO document whether misc is a string or dict or it can be both
    def create_multiword_token(self, words=None, form=None, misc=None):
        """Create and return a new multi-word token (MWT) in this tree.

        The new MWT can be optionally initialized using the following args.
        Args:
        words: a list of nodes which are part of the new MWT
        form: string representing the surface form of the new MWT
        misc: misc attribute of the new MWT
        """
        mwt = MWT(words, form, misc, root=self)
        self._mwts.append(mwt)
        return mwt

    @property
    def multiword_tokens(self):
        """Return a list of all multi-word tokens in this tree."""
        return self._mwts

    # TODO should this setter be part of the public API?
    @multiword_tokens.setter
    def multiword_tokens(self, mwts):
        """Set the list of all multi-word tokens in this tree."""
        self._mwts = mwts

    def get_sentence(self, if_missing='detokenize'):
        """Return either the stored `root.text` or (if None) `root.compute_text()`.

        Args:
        if_missing: What to do if `root.text` is `None`? (default=detokenize)
         * `detokenize`: use `root.compute_text()` to compute the sentence.
         * `empty`: return an empty string
         * `warn_detokenize`, `warn_empty`: in addition emit a warning via `logging.warning()`
         * `fatal`: raise an exception
        """
        sentence = self.text
        if sentence is not None:
            return sentence
        if if_missing == 'fatal':
            raise RuntimeError('Tree %s has empty root.text.' % self.address())
        if if_missing.startswith('warn'):
            logging.warning('Tree %s has empty root.text.', self.address())
        if if_missing.endswith('detokenize'):
            return self.compute_text()
        return ''

    def add_comment(self, string):
        """Add a given `string` to `root.comment` separated by a newline and space."""
        if self.comment is None:
            self.comment = string
        else:
            self.comment = self.comment.rstrip() + "\n " + string

    @property
    def token_descendants(self):
        """Return all tokens (one-word or multi-word) in the tree.

        ie. return a list of `core.Node` and `core.MWT` instances,
        whose forms create the raw sentence. Skip nodes, which are part of multi-word tokens.

        For example with:
        1-2    vámonos   _
        1      vamos     ir
        2      nos       nosotros
        3-4    al        _
        3      a         a
        4      el        el
        5      mar       mar

        `[n.form for n in root.token_descendants]` will return `['vámonos', 'al', 'mar']`.
        """
        result = []
        last_mwt_id = 0
        for node in self._descendants:
            mwt = node.multiword_token
            if mwt:
                if node.ord > last_mwt_id:
                    last_mwt_id = mwt.words[-1].ord
                    result.append(mwt)
            else:
                result.append(node)
        return result

    @property
    def descendants_and_empty(self):
        return sorted(self._descendants + self.empty_nodes)

    def steal_nodes(self, nodes):
        """Move nodes from another tree to this tree (append)."""
        old_root = nodes[0].root
        for node in nodes[1:]:
            if node.root != old_root:
                raise ValueError("steal_nodes(nodes) was called with nodes from several trees")
        nodes = sorted(nodes)
        whole_tree = nodes == old_root.descendants
        new_ord = len(self._descendants)
        # pylint: disable=protected-access
        for node in nodes:
            new_ord += 1
            node.ord = new_ord
            node._root = self
            if not whole_tree:
                for child in [n for n in node.children if n not in nodes]:
                    child._parent = old_root
                    old_root._children = sorted(old_root.children + [child])
                node._children = [n for n in node.children if n in nodes]
            if node.parent == old_root or (not whole_tree and node.parent not in nodes):
                node.parent._children = [n for n in node.parent._children if n != node]
                node._parent = self
                self._children.append(node)
        if whole_tree:
            old_root._descendants = []
            self._mwts += old_root.multiword_tokens
            old_root.multiword_tokens = []
        else:
            old_root._descendants = [n for n in old_root._descendants if n not in nodes]
            mwt = node.multiword_token
            for node in nodes:
                if mwt:
                    words = [w for w in mwt.words if w in nodes]
                    mwt.remove()
                    self.create_multiword_token(words=words, form=mwt.form, misc=mwt.misc)
        self._descendants += nodes
        # pylint: enable=protected-access
