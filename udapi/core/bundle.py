"""Bundle class represents one sentence."""

import re

from udapi.core.root import Root
from udapi.block.write.textmodetrees import TextModeTrees

VALID_ZONE_REGEX = re.compile("^[a-z-]*(_[A-Za-z0-9-]+)?$")


class Bundle(object):
    """Bundle represents one sentence in an UD document.

    A bundle contains one or more trees. More trees are needed e.g. in case of
    parallel treebanks where each tree represents a translation of the sentence
    in a different languages.
    Trees in one bundle are distinguished by a zone label.
    """

    __slots__ = ["trees", "number", "_bundle_id", "_document"]

    def __init__(self, bundle_id=None, document=None):
        self.trees = []
        self._bundle_id = bundle_id
        self._document = document

    @property
    def bundle_id(self):
        """ID of this bundle."""
        return self._bundle_id

    @bundle_id.setter
    def bundle_id(self, bundle_id):
        self._bundle_id = bundle_id
        if len(self.trees) == 1 and self.trees[0].zone == '':
            self.trees[0]._sent_id = bundle_id
        else:
            for tree in self.trees:
                tree._sent_id = bundle_id + '/' + tree.zone  # pylint: disable=protected-access

    def __str__(self):
        if self.bundle_id is None:
            return 'bundle without id'
        return "bundle id='%s'" % self.bundle_id

    def __iter__(self):
        return iter(self.trees)

    @property
    def document(self):
        """Returns the document in which the bundle is contained."""
        return self._document

    def get_tree(self, zone=''):
        """Returns the tree root whose zone is equal to zone."""
        trees = [tree for tree in self.trees if tree.zone == zone]
        if len(trees) == 1:
            return trees[0]
        elif len(trees) == 0:
            raise Exception("No tree with zone=" + zone + " in the bundle")
        else:
            raise Exception("More than one tree with zone=" +
                            zone + " in the bundle")

    def has_tree(self, zone=''):
        """Does this bundle contain a tree with a given zone?"""
        for tree in self.trees:
            if tree.zone == zone:
                return True
        return False

    def create_tree(self, zone=None):
        """Return the root of a newly added tree with a given zone."""
        root = Root()
        root.zone = zone
        self.add_tree(root)
        return root

    def check_zone(self, new_zone):
        """Raise an exception if the zone is invalid or already exists."""
        if not VALID_ZONE_REGEX.match(new_zone):
            raise ValueError("'{}' is not a valid zone name ({})".format(
                new_zone, VALID_ZONE_REGEX.pattern))
        if new_zone == 'all':
            raise ValueError("'all' cannot be used as a zone name")
        if new_zone in [x.zone for x in self.trees]:
            raise Exception("Tree with zone '%s' already exists in %s" % (new_zone, self))

    def add_tree(self, root):
        """Add an existing tree to the bundle."""
        if root.zone is None:
            root.zone = ''
        self.check_zone(root.zone)
        root.bundle = self
        self.trees.append(root)
        doc_json = root.json.get('__doc__')
        if doc_json:
            self._document.json.update(doc_json)
            del root.json['__doc__']
        return root

    def remove(self):
        """Remove a bundle from the document."""
        self._document.bundles = [bundle for bundle in self._document.bundles if bundle != self]
        for i, bundle in enumerate(self._document.bundles):
            bundle.number = i

    def address(self):
        """Return bundle_id or '?' if missing."""
        return self.bundle_id if self.bundle_id is not None else '?'

    def draw(self, **kwargs):
        """Pretty print the trees using TextModeTrees."""
        TextModeTrees(**kwargs).process_bundle(self)
