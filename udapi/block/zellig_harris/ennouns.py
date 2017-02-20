import logging

from udapi.core.block import Block

from udapi.block.zellig_harris.configurations import *
from udapi.block.zellig_harris.queries import *

class EnNouns(Configurations):
    """
    A block for extraction context configurations for English nouns.
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
        super(EnNouns, self).__init__(args)

    def process_node(self, node):
        """
        Extract context configurations for English nouns.

        :param node: A node to be process.

        """
        # We want to extract contexts only for verbs.
        if str(node.upostag) not in self.pos:
            return

        if self.verbose:
            logging.info('')
            logging.info('Processing node %s/%s', node.root.sent_id, node)

        #self.apply_query('en_verb_mydobj', node)
        self.apply_query('en_noun_is_subj_relcl', node)