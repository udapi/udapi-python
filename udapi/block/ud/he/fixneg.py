"""Block ud.he.FixNeg fix remaining deprel=neg

Author: Martin Popel
"""
import logging

from udapi.core.block import Block


class FixNeg(Block):
    """Block for fixing the remaining cases (after ud.Convert1to2) of deprel=neg in UD_Hebrew."""

    def process_node(self, node):
        # אינם is a negative copula verb
        if node.deprel == 'neg':
            if node.feats['VerbType'] == 'Cop':
                node.upos = 'AUX'
                node.deprel = 'cop'
                # I think deprel=cop Polarity=Neg is enough and VerbType=Cop is not needed
                del node.feats['VerbType']
                # This way we have solved the ToDo=neg
                if node.misc['ToDo'] == 'neg':
                    del node.misc['ToDo']
            else:
                logging.warning("Strange node %s with deprel=neg", node)
