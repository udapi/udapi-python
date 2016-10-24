#!/usr/bin/env python

import codecs
import re

from node import Node
from root import Root

class Bundle(object):
    """
    Bundle can be used for embracing two or more Universal Dependency trees that are associated in some way
    (e.g. parallel translations) inside a document. Unless different zones are differentiated in a bundle,
    there's only one tree per bundle by default.

    """

    __slots__ = [ "trees", "number", "id", "_aux", "_document" ]

    def document(self):
        """returns the document in which the bundle is contained"""
        return self._document

    def __init__(self):
        self.trees = []

    def __iter__(self):
        return iter(self.trees)

    def get_tree(self, zone):
        """returns the tree root whose zone is equal to zone"""

        trees = [tree for tree in self.trees if tree.zone == zone]
        if len(trees) == 1:
            return trees[0]
        elif len(trees) == 0:
            raise Exception( "No tree with zone="+zone+" in the bundle")
        else:
            raise Exception("More than one tree with zone="+zone+" in the bundle")


    def _check_new_zone(self,root,new_zone):
        for root in root.bundle.trees:
            if root != changed_root and root.zone == zone:
                 raise Exception("Zone "+zone+" already exists in the bundle")


    def create_tree(self,zone=None):
        """returns the root of a newly added tree whose zone is equal to zone"""
        root = Root()
        root.set_zone(zone)
        root._bundle = self
        self.add_tree(root)
        return root

    def add_tree(self, root):
        """add an existing tree to the bundle"""
        root._bundle = self

        self._check_new_zone(root, root.zone)
        self.trees.append(root)
        return root

    def remove(self):
        "remove a bundle from the document"
        document.bundles = [bundle for bundle in document.bundles if not bundle == self]
