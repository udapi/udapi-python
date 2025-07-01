"""Block ud.ro.FixFixed

Author: Dan Zeman
"""
import logging

from udapi.core.block import Block


class FixFixed(Block):
    """Block for fixing verbal 'fixed' expressions."""

    def process_node(self, node):
        fixchildren = [x for x in node.children if x.udeprel=='fixed']
        nfc = len(fixchildren)
        if nfc>0 and node.udeprel=="advmod":
            node.feats['ExtPos'] = 'ADV'
        #elif nfc>0:
        #    logging.info('Another case: '+node.lemma+' '+' '.join([x.form for x in fixchildren]))
