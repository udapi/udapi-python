"""Block to convert spurious auxiliaries to lexical verbs in Kazakh."""
from udapi.core.block import Block
import logging
import re

class FixSpuriousAux(Block):

    def process_node(self, node):
        """
        Some verbs that are called auxiliary by the traditional grammar, should
        be analyzed in UD as VERB + non-finite xcomp.
        """
        if node.upos == 'AUX' and node.udeprel == 'aux':
            # баста = start
            if re.match(r'^(баста|кет)$', node.lemma):
                node.upos = 'VERB'
                # The auxiliary inherits the incoming relation of its original parent.
                lexverb = node.parent
                node.parent = lexverb.parent
                node.deprel = lexverb.deprel
                # The auxiliary also inherits some but not all children of the lexical verb.
                for c in lexverb.children:
                    if re.match(r'^(nsubj|csubj|obl|advmod|advcl|vocative|discourse|parataxis|punct)$', c.udeprel):
                        c.parent = node
                # The lexical verb becomes an xcomp of the auxiliary.
                lexverb.parent = node
                lexverb.deprel = 'xcomp'
