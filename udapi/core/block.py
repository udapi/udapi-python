#!/usr/bin/env python

class Block(object):
    """The smallest processing unit for processing Universal Dependencies data."""

    def __init__(self,args = {}):
        pass

    def process_start(self):
        """A hook method that is executed before processing UD data"""
        pass

    def process_end(self):
        """A hook method that is executed after processing all UD data"""
        pass

    def process_node(self, node):
        """Process a UD node"""
        raise Exception("No processing activity defined in block "+str(self))

    def process_tree(self,tree):
        """Process a UD tree"""
        for node in tree.descendants():
            self.process_node(node)

    def process_bundle(self,bundle):
        """Process a UD bundle"""
        for tree in bundle:
            self.process_tree(tree)

    def process_document(self,document):
        """Process a UD document"""
        for bundle in document.bundles:
            self.process_bundle(bundle)

