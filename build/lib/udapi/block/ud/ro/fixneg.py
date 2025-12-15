"""Block ud.ro.FixNeg ad-hoc fixes

Author: Martin Popel
"""
import logging

from udapi.core.block import Block


class FixNeg(Block):
    """Block for fixing the remaining cases (after ud.Convert1to2) of deprel=neg in UD_Romanian."""

    def process_node(self, node):
        if node.deprel == "neg":
            if node.upos == "PRON" and node.form == "ne":
                node.feats = 'Polarity=Neg'  # delete other features
            elif node.upos != "ADJ":
                logging.warning("Strange node %s with deprel=neg", node)
            node.upos = "ADV"
            node.deprel = "advmod"
