#!/usr/bin/env python

from udapi.core.block import Block


class Vulic(Block):
    """
    A block for extraction context configurations for training verb representations using word2vecf.

    """

    def __init__(self, args=None):
        """
        Initialization.

        :param args: A dict of optional parameters.

        """
        if args is None:
            args = {}

        self.pool = ['prep', 'acl', 'obj', 'comp', 'adc']
        if 'pool' in args:
            self.pool = args['pool'].split(',')

    def process_node(self, node):
        """
        Extract context configuration for verbs according to (Vulic et al., 2016).

        :param node: A node to be process.

        """
        # We want to extract contexts only for verbs.
        if str(node.upostag) != "VERB":
            return

        # Process node's parent.
        if node.parent.deprel in self.pool:
            parent = node.parent
            print "%s %s_%s" % (node.form[:-3], parent.form[:-3], node.deprel)

        # Process node's childs.
        for child in node.descendants():
            if child.deprel in self.pool:
                print "%s %s_%s" % (node.form[:-3], child.form[:-3], child.deprel)
