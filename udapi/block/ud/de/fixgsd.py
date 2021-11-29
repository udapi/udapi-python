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
            if node.prev_node and re.match(r'^\d+$', node.prev_node.form) and node.prev_node.no_space_after:
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
        # Even if the digits and the period are already in one token, check their annotation.
        if re.match(r'^\d+\.$', node.form):
            node.lemma = node.form
            node.upos = 'ADJ'
            node.xpos = 'ADJA'
            node.feats = '_'
            node.feats['NumType'] = 'Ord'
            if node.udeprel == 'nummod':
                node.deprel = 'amod'
        # Finally, make sure that ordinal numerals expressed verbosely are tagged properly.
        # Unlike for digits, do not remove the features for Gender, Number, and Case.
        # Skip 'acht' because we cannot reliably distinguish it from the cardinal numeral and from the verb 'achten'.
        if re.match(r'^(erst|zweit|dritt|viert|fünft|sechst|siebt|neunt|(drei|vier|fünf|sechs|sieb|acht|neun)?zehnt|elft|zwölft)(er)?$', node.lemma, re.IGNORECASE):
            # Skip 'erst' that is used as an adverb.
            if node.lemma != 'erst' or node.upos != 'ADV':
                node.lemma = re.sub(r'^(.+)er$', r'\1', node.lemma)
                node.upos = 'ADJ'
                node.xpos = 'ADJA'
                node.feats['NumType'] = 'Ord'
                if node.udeprel == 'nummod':
                    node.deprel = 'amod'
