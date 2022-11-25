"""Block to add missing lemmas in cases where it seems obvious what the lemma should be."""
from udapi.core.block import Block
import logging
import re

class Lemmatize(Block):

    # dictionary: form --> lemma
    lemma = {
        # The plural suffix -men.
        '我們':   '我', # trad
        '我们':   '我', # simp
        '他們':   '他', # trad
        '他们':   '他', # simp
        '它們':   '它', # trad
        '它们':   '它', # simp
        '牠們':   '牠', # trad
        '她們':   '她', # trad
        '她们':   '她', # simp
        '人們':   '人', # trad
        '人们':   '人'  # simp
    }

    def process_node(self, node):
        """
        Parts of the Chinese treebanks lack lemmas. Fortunately, lemmatization
        of Sino-Tibetan languages is pretty straightforward most of the time,
        as the lemma typically equals to the actual word form.
        """
        if node.lemma == '' or node.lemma == '_' and node.form != '_' and node.feats['Typo'] != 'Yes':
            if node.form in self.lemma:
                node.lemma = self.lemma[node.form]
            else:
                node.lemma = node.form
