import logging

from udapi.core.block import Block

from udapi.block.zellig_harris.configurations import *
from udapi.block.zellig_harris.queries import *


class EnVerbs(Configurations):
    """
    A block for extraction context configurations for English verbs.

    The configurations will be used as the train data for obtaining
    the word representations using word2vecf.
    """

    def process_node(self, node):
        """
        Extract context configurations for English verbs.

        :param node: A node to be process.

        """
        # We want to extract contexts only for verbs.
        if str(node.upos) not in self.pos:
            return

        if self.verbose:
            logging.info('')
            logging.info('Processing node %s/%s', node.root.sent_id, node)

        self.apply_query('en_verb_mydobj', node)
