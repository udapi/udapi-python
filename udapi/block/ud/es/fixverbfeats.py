"""Block to fix features (and potentially lemmas) of verbs in UD Spanish-PUD."""
from udapi.core.block import Block
import logging
import re

class FixVerbFeats(Block):

    def process_node(self, node):
        """
        The features assigned to verbs in Spanish PUD are often wrong, although
        the annotation was (reportedly) done manually. For example, infinitives
        are tagged with VerbForm=Fin instead of VerbForm=Inf.
        """
        if re.match(r'^(VERB|AUX)$', node.upos):
            if re.search(r'[aei]r$', node.form, re.IGNORECASE):
                # The infinitive has no features other than VerbForm.
                node.feats = {}
                node.feats['VerbForm'] = 'Inf'
                node.lemma = node.form.lower()
