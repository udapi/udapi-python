"""Block ud.ro.FixFixed

Author: Dan Zeman
"""
import logging

from udapi.core.block import Block


class FixFixed(Block):
    """Block for fixing annotation of some 'fixed' expressions."""

    def process_node(self, node):
        fixchildren = [x for x in node.children if x.udeprel=='fixed']
        nfc = len(fixchildren)
        if nfc > 0:
            if node.udeprel == 'advmod' and node.feats['ExtPos'] == '':
                node.feats['ExtPos'] = 'ADV'
            elif node.feats['ExtPos'] == '':
                logging.info('Another case: '+node.lemma+' '+' '.join([x.form for x in fixchildren]))
