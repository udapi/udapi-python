"""
Block to fix annotation of UD German-GSD.
"""
from udapi.core.block import Block
import logging
import re

class FixGSD(Block):

    def process_node(self, node):
        """
        Normalizes tokenization, lemmatization and tagging of ordinal numerals
        that are expressed using digits followed by a period.
        https://github.com/UniversalDependencies/UD_German-GSD/issues/24
        """
        # Ignore periods that terminate a sentence, although they could belong
        # to an ordinal numeral at the same time.
        if node.form == '.' and node.next_node:
            # Ignore number+period combinations that have an intervening space.
            if node.prev_node and re.match('^\d+$', node.prev_node.form) and node.prev_node.no_space_after:
                # Merge the number and the period into one token.
                number = node.prev_node
                period = node
                # The period should not have any children but if it does, re-attach them to the number.
                for c in period.children:
                    c.parent = number
                # The period should be followed by a space but if it isn't, mark it at the number.
                number.misc['SpaceAfter'] = 'No' if period.no_space_after else ''
                number.form += '.'
                number.lemma = number.form
                number.upos = 'ADJ'
                number.xpos = 'ADJA'
                number.feats = '_'
                number.feats['NumType'] = 'Ord'
                if number.udeprel == 'nummod':
                    number.deprel = 'amod'
                period.remove()
