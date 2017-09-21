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
        #if str(node.upos) not in self.pos:
        #    return

        if self.verbose:
            logging.info('')
            logging.info('Processing node %s/%s', node.root.sent_id, node)
           # logging.info('Processing node %s/%s', node.root.sent_id, node)



        if str(node.upos) == 'NOUN':
            self.apply_query('en_verbs_001a_der_ADJx_N1__V1_ADVx', node,['neg_prefix','suffix','pos_conversion'],['neg_prefix','suffix','pos_conversion'],['halucinate'])
            self.apply_query('en_verbs_002b_der_Nx_N1__V1_Nx',node,['neg_prefix','suffix','pos_conversion'],None,['halucinate'])
            self.apply_query('en_verbs_004b_der_N1_prepNx__V1_prepNx',node,['neg_prefix','suffix','pos_conversion'],None,['halucinate'])

            self.apply_query('en_verbs_002b_003a_V1_Nx', node, None, None, None)
            self.apply_query('en_verbs_004b_V1_prepNx', node, None, None, None)
        if str(node.upos) == 'ADJ':
            self.apply_query('en_verbs_003a_der_ADJ1_Nx__V1_Nx',node,['neg_prefix','suffix','pos_conversion'],None,['halucinate'])

        if str(node.upos) == 'VERB':
            self.apply_query('en_verbs_001a_V1_ADVx', node, None, None, None)



       # self.apply_query('en_verb_has_iobj_is_relclActive', node)
       # self.apply_query('en_verb_has_iobj_is_relclPassive', node)
       # self.apply_query('en_verb_has_dobj_is_relclPassive', node)
       # self.apply_query('en_verb_has_dobj_is_relclActive', node)


