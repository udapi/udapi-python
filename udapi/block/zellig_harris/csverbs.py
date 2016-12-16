#!/usr/bin/env python

import logging

from udapi.core.block import Block

from common import *
from queries import *


class CsVerbs(Block):
    """
    A block for extraction context configurations for Czech verbs.
    The configurations will be used as the train data for obtaining the word representations using word2vecf.

    """

    def __init__(self, args=None):
        """
        Initialization.

        :param args: A dict of optional parameters.

        """
        if args is None:
            args = {}

        # Call the constructor of the parent object.
        super(CsVerbs, self).__init__(args)

        # Process the 'POS' argument.
        self.pos = []
        if 'pos' in args:
            self.pos = args['pos'].split(',')

        # Process the 'print_lemmas' argument.
        self.print_lemmas = False
        if 'print_lemmas' in args and args['print_lemmas'] == '1':
            self.print_lemmas = True

        # Process the 'print_lemmas' argument.
        self.verbose = False
        if 'verbose' in args and args['verbose'] == '1':
            self.verbose = True

    def process_node(self, node):
        """
        Extract context configuration for verbs according to (Vulic et al., 2016).

        :param node: A node to be process.

        """
        # We want to extract contexts only for verbs.
        if str(node.upostag) not in self.pos:
            return

        if self.verbose:
            logging.info('Processing node %s/%s', node.root.sent_id, node)

        # Apply the set of queries and extract the configurations.
        try:
            for (node_a, relation_name, node_b) in en_verb_mydobj(node):
                print_triple(node_a, relation_name, node_b, print_lemma=self.print_lemmas)
        except ValueError as exception:
            if self.verbose:
                logging.info('No configurations for node %s/%s: %s', node.root.sent_id, node, exception)

            pass


