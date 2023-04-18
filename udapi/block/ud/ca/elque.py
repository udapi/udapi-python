"""
This block searches for relative clauses modifying a determiner ('el que...').
It is written for Catalan but a similar block should work for Spanish and other
Romance languages.
"""
from udapi.core.block import Block
import logging
import re

class ElQue(Block):

    def process_node(self, node):
        # We take 'que' as the central node of the construction.
        if node.lemma == 'que' and node.upos == 'PRON' and node.parent.ord > node.ord:
            # We will refer to the parent of 'que' as a verb, although it can be
            # a non-verbal predicate, too.
            que = node
            verb = node.parent
            # Check the lemma of the determiner. The form may vary for gender and number.
            if que.prev_node and que.prev_node.lemma == 'el':
                el = que.prev_node
                stanford = []
                adp = None
                if el.prev_node and el.prev_node.upos == 'ADP':
                    adp = el.prev_node
                    if adp.udeprel == 'fixed':
                        adp = adp.parent
                    parentstr = 'OTHER'
                    if adp.parent == el:
                        parentstr = 'el'
                    elif adp.parent == que:
                        parentstr = 'que'
                    elif adp.parent == verb:
                        parentstr = 'VERB'
                    stanford.append(adp.deprel + '(' + parentstr + ', ADP)')
                if el.parent == adp:
                    parentstr = 'ADP'
                elif el.parent == que:
                    parentstr = 'que'
                elif el.parent == verb:
                    parentstr = 'VERB'
                else:
                    parentstr = 'OTHER'
                stanford.append(el.deprel + '(' + parentstr + ', el)')
                stanford.append(que.deprel + '(VERB, que)')
                if verb.parent == adp:
                    parentstr = 'ADP'
                elif verb.parent == el:
                    parentstr = 'el'
                else:
                    parentstr = 'OTHER'
                stanford.append(verb.deprel + '(' + parentstr + ', VERB)')
                print('; '.join(stanford))
