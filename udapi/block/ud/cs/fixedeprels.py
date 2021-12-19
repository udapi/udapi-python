"""Block to fix case-enhanced dependency relations in Czech."""
from udapi.core.block import Block
import logging
import re

class FixEdeprels(Block):

    def process_node(self, node):
        """
        Occasionally the edeprels automatically derived from the Czech basic
        trees do not match the whitelist. For example, the noun is an
        abbreviation and its morphological case is unknown.
        """
        for edep in node.deps:
            if edep['deprel'] eq 'nmod:na':
                # The case is unknown. We need 'acc' or 'loc'.
                # The locative is probably more frequent but it is not so likely with every noun.
                if re.match(r'^(adresát|AIDS|DEM|frank|h|ha|hodina|Honolulu|jméno|koruna|litr|metr|míle|miliarda|milión|mm|MUDr|NATO|obyvatel|OSN|počet|procento|příklad|rok|SSSR|vůz)$', node.lemma):
                    edep['deprel'] = 'nmod:na:acc'
                else
                    edep['deprel'] = 'nmod:na:loc'
