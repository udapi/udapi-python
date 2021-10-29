"""Block to fix tokenization of exclamation marks in UD Spanish-AnCora."""
from udapi.core.block import Block
import logging
import re

class FixExclamation(Block):

    def process_node(self, node):
        """
        In Spanish AnCora, there are things like '¡Hola!' as one token.
        The punctuation should be separated. One may question whether this
        should include names of companies (Yahoo!) or products (la revista
        Hello!) but it should, as company and product names often have
        multiple tokens (even multiple full words, not just punctuation)
        and these are also separated in UD.
        """
        if re.search(r'^[¡!]\w', node.form):
            # Separate the punctuation and attach it to the rest.
            punct = node.create_child()
            punct.shift_before_node(node)
            punct.form = node.form[:1]
            node.form = node.form[1:]
            punct.lemma = punct.form
            punct.upos = 'PUNCT'
            punct.xpos = 'faa' if punct.form == '¡' else 'fat'
            punct.feats['PunctType'] = 'Excl'
            punct.feats['PunctSide'] = 'Ini' if punct.form == '¡' else 'Fin'
            punct.misc['SpaceAfter'] = 'No'
            punct.deprel = 'punct'
            # Mark the position for manual check.
            node.misc['Mark'] = 'PunctSep'
        if re.search(r'\w[¡!]$', node.form):
            # Separate the punctuation and attach it to the rest.
            punct = node.create_child()
            punct.shift_after_node(node)
            punct.form = node.form[-1:]
            node.form = node.form[:-1]
            punct.lemma = punct.form
            punct.upos = 'PUNCT'
            punct.xpos = 'faa' if punct.form == '¡' else 'fat'
            punct.feats['PunctType'] = 'Excl'
            punct.feats['PunctSide'] = 'Ini' if punct.form == '¡' else 'Fin'
            punct.misc['SpaceAfter'] = node.misc['SpaceAfter']
            node.misc['SpaceAfter'] = 'No'
            punct.deprel = 'punct'
            # Mark the position for manual check.
            node.misc['Mark'] = 'PunctSep'
