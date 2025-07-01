"""Block ud.ro.FixFixed

Author: Dan Zeman
"""
import logging

from udapi.core.block import Block


class FixFixed(Block):
    """Block for fixing verbal 'fixed' expressions."""

    def process_node(self, node):
        if node.upos=='VERB':
            fixchildren = [x for x in node.children if x.udeprel=='fixed']
            nfc = len(fixchildren)
            if nfc==1 and fixchildren[0].upos == 'NOUN':
                fixchildren[0].deprel = 'obj'
            elif nfc==2 and fixchildren[1].upos == 'NOUN':
                fixchildren[0].parent = fixchildren[1]
                fixchildren[0].deprel = 'case'
                fixchildren[1].deprel = 'obl'
            elif nfc>0:
                logging.info('Another case: '+node.lemma+' '+' '.join([x.form for x in fixchildren]))
