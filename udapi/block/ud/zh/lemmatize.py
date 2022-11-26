"""Block to add missing lemmas in cases where it seems obvious what the lemma should be."""
from udapi.core.block import Block
import logging
import re

class Lemmatize(Block):

    def __init__(self, rewrite='empty', **kwargs):
        """
        Create the ud.zh.Lemmatize block instance.

        Args:
        rewrite=empty: set the lemma if it was empty so far; do not touch the rest
        rewrite=form: set the lemma if it was empty or equal to form; do not touch the rest
        rewrite=all: set the lemma regardless of what it was previously
        """
        super().__init__(**kwargs)
        if not re.match(r'^(empty|form|all)$', rewrite):
            raise ValueError("Unexpected value of parameter 'rewrite'")
        self.rewrite = rewrite

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
        if self.rewrite == 'empty' and not (node.lemma == '' or node.lemma == '_' and node.form != '_' and node.feats['Typo'] != 'Yes'):
            return
        elif self.rewrite == 'form' and not (node.lemma == node.form or node.lemma == '' or node.lemma == '_' and node.form != '_' and node.feats['Typo'] != 'Yes'):
            return
        # Verbs that are derived from the copula and tagged as the copula need
        # to have the lemma of the copula (是 shì).
        if re.search(r'是', node.form) and re.match(r'^(AUX|VERB)$', node.upos):
            node.lemma = '是'
            if node.form == '不是':
                node.feats['Polarity'] = 'Neg'
        elif node.form in self.lemma:
            node.lemma = self.lemma[node.form]
        else:
            node.lemma = node.form
