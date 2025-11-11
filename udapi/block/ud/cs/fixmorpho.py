"""
A Czech-specific block to fix lemmas, UPOS and morphological features in UD.
It should increase consistency across the Czech treebanks. It focuses on
individual closed-class verbs (such as the auxiliary "být") or on entire classes
of words (e.g. whether or not nouns should have the Polarity feature). It was
created as part of the Hičkok project (while importing nineteenth-century Czech
data) but it should be applicable on any other Czech treebank.
"""
from udapi.core.block import Block
import logging
import re

class FixMorpho(Block):

    def process_node(self, node):
        # Do not touch words marked as Foreign or Typo. They may not behave the
        # way we expect in Czech data.
        if node.feats['Foreign'] == 'Yes' or node.feats['Typo'] == 'Yes':
            return
        # Nouns do not have polarity but the Prague-style tagsets may mark it.
        if node.upos in ['NOUN', 'PROPN']:
            if node.feats['Polarity'] == 'Pos':
                node.feats['Polarity'] = ''
            elif node.feats['Polarity'] == 'Neg':
                logging.warn(f'To remove Polarity=Neg from the NOUN {node.form}, we may have to change its lemma ({node.lemma}).')
        # In 19th century data, the grammaticalized usages of "se", "si" are
        # tagged as PART (rather than a reflexive PRON, which is the standard).
        # Even if it already was tagged PRON, some features may have to be added.
        if node.upos in ['PRON', 'PART'] and node.form.lower() in ['se', 'si']:
            node.lemma = 'se'
            node.upos = 'PRON'
            node.feats['PronType'] = 'Prs'
            node.feats['Reflex'] = 'Yes'
            if node.form.lower() == 'se':
                # Occasionally "se" can be genitive: "z prudkého do se dorážení".
                if not node.feats['Case'] == 'Gen':
                    node.feats['Case'] = 'Acc'
            else:
                node.feats['Case'] = 'Dat'
            node.feats['Variant'] = 'Short'
        # In Czech UD, "být" is always tagged as AUX and never as VERB, regardless
        # of the fact that it can participate in purely existential constructions
        # where it no longer acts as a copula. Czech tagsets typically do not
        # distinguish AUX from VERB, which means that converted data may have to
        # be fixed.
        if node.upos == 'VERB' and node.lemma == 'být':
            node.upos = 'AUX'
