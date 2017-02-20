import logging

from udapi.core.block import Block

from udapi.block.zellig_harris.common import *
from udapi.block.zellig_harris.queries import *


class Configurations(Block):
    """
    An abstract class for four extracting scenarios.

    """

    def __init__(self, pos=None, print_lemmas=None, verbose=None):
        """
        Initialization.

        :param args: A dict of optional parameters.

        """
        # Call the constructor of the parent object.
        super(Configurations, self).__init__()

        # Process the 'POS' argument.
        self.pos = []
        if pos is not None:
            self.pos = pos.split(',')

        # Process the 'print_lemmas' argument.
        self.print_lemmas = False
        if print_lemmas is not None and print_lemmas == 1:
            self.print_lemmas = True

        # Process the 'print_lemmas' argument.
        self.verbose = False
        if verbose is not None and verbose == 1:
            self.verbose = True

    def apply_query(self, query_id, node):
        """
        A generic method for applying a specified query on a specified node.

        :param query_id: A name of the query method to be called.
        :param node: An input node.

        """
        if self.verbose:
            logging.info(' - applying query %s', query_id)

        try:
            methods = globals()
            method = methods.get(query_id)
        except Exception as exception:
            logging.critical(' - no such query %s', query_id)
            raise RuntimeError('No such query %s' % query_id)

        triples = []
        try:
            triples = method(node)
        except ValueError as exception:
            if self.verbose:
                logging.info(' - no configurations: %s', exception)

        if len(triples) == 0:
            if self.verbose:
                logging.info(' - no configurations, but all conditions passed.')

        for (node_a, relation_name, node_b) in triples:
            triple = print_triple(node_a, relation_name, node_b, print_lemma=self.print_lemmas)

            if self.verbose:
                logging.info(' - %s', triple)

            print(triple)

    def process_tree(self, tree):
        """
        If required, print detailed info about the processed sentence.

        :param tree: A sentence to be processed.

        """
        if self.verbose:
            logging.info('')
            logging.info('---')
            logging.info('Sentence ID : %s', tree.address())
            logging.info('Sentence    : %s', ' '.join([node.form for node in tree.descendants()]))
            logging.info('---')

        for node in tree.descendants():
            self.process_node(node)

    def process_node(self, node):
        """
        Extract context configuration for verbs according to (Vulic et al., 2016).

        :param node: A node to be process.

        """
        raise NotImplementedError('Cannot call this abstract method.')
