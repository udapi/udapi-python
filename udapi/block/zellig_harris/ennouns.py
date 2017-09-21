import logging
from udapi.core.block import Block
from udapi.block.zellig_harris.configurations import *
from udapi.block.zellig_harris.queries import *


class EnNouns(Configurations):

    """
    A block for extraction context configurations for English nouns.

    The configurations will be used as the train data for obtaining
    the word representations using word2vecf.
    """

    def process_node(self, node):
        """
        Extract context configurations for English nouns.

        :param node: A node to be process.

        """
        # We want to extract contexts only for nouns.
        #if str(node.upos) not in self.pos:
         #   return

        if self.verbose:
            logging.info('')
            logging.info('Processing node %s/%s', node.root.address(), node)

        if str(node.upos) == 'VERB':
           self.apply_query('en_nouns_001b_der_V1_ADVx__ADJx_N1', node,['neg_prefix','suffix','pos_conversion'], ['neg_prefix','suffix','pos_conversion'],['halucinate'])
        if str(node.upos) == 'NOUN':
            self.apply_query('en_nouns_002a_der_V1_NX__Nx_N1', node, ['neg_prefix', 'suffix', 'pos_conversion'], None, ['halucinate'])
            self.apply_query('en_nouns_003b_der_V1_Nx__ADJ1_Nx', node, ['neg_prefix', 'suffix', 'pos_conversion'], None, ['halucinate'])
            self.apply_query('en_nouns_004a_der_V1_prepNX__N1_prepNx', node, ['neg_prefix', 'suffix', 'pos_conversion'], None, ['halucinate'])
            self.apply_query('en_nouns_005_Nx_ADJ1__Nx_neg_ADJ1', node, ['neg_prefix', 'suffix', 'pos_conversion'], None, ['halucinate'])

            self.apply_query('en_nouns_001b_003b_005_ADJx_N1',node, None, None,None)
            self.apply_query('en_nouns_002a_Nx_N1', node, None, None, None)
            self.apply_query('en_nouns_004a_N1_prepNx',node, None, None, None)

        if str(node.upos) == 'PROPN':
            self.apply_query('en_nouns_005_Nx_ADJ1__Nx_neg_ADJ1', node, ['neg_prefix', 'suffix', 'pos_conversion'], None, ['halucinate'])
            self.apply_query('en_nouns_001b_003b_005_ADJx_N1', node, None, None, None)