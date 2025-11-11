"""
A Czech-specific block to fix lemmas, UPOS and morphological features in UD.
It should increase consistency across the Czech treebanks. It focuses on
individual closed-class verbs (such as the auxiliary "být") or on entire classes
of words (e.g. whether or not nouns should have the Polarity feature). It was
created as part of the Hičkok project (while importing nineteenth-century Czech
data) but it should be applicable on any other Czech treebank.
"""
import udapi.block
import re

class FixMorpho(udapi.block):

    def process_node(self, node):
        # In Czech UD, "být" is always tagged as AUX and never as VERB, regardless
        # of the fact that it can participate in purely existential constructions
        # where it no longer acts as a copula. Czech tagsets typically do not
        # distinguish AUX from VERB, which means that converted data may have to
        # be fixed.
        if node.upos == 'VERB' and node.lemma == 'být':
            node.upos = 'AUX'
