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
        # Lemmatize negated verbs to their affirmative forms.
        # 不是 bùshì = not be
        # 沒有 没有 méiyǒu = not exist
        # 沒能 没能 méinéng = cannot
        # 未能 wèinéng = cannot
        # Lemmatize question verbs to their base forms.
        # 要不要 yàobùyào = do (you) want?
        # 有没有 yǒuméiyǒu = do (you) have?
        # Verbs that are derived from the copula and tagged as the copula need
        # to have the lemma of the copula (是 shì 爲 為 为 wèi/wéi).
        # 亦為 亦为 yìwèi = také
        # 則為 则为 zéwèi = potom
        # 更為 更为 gèngwèi = více
        # 認為 认为 rènwéi = myslet, věřit
        # 以為 以为 yǐwéi = myslet, věřit
        # 以爲 以为 yǐwéi = myslet, věřit
        if re.match(r'^(AUX|VERB)$', node.upos):
            m1 = re.match(r'^([不没沒未])(.+)$', node.form)
            m2 = re.match(r'^(.+)([不没沒未])\1$', node.form)
            m3 = re.search(r'([是爲為为])', node.form)
            if m1:
                node.lemma = m1.group(2)
                node.feats['Polarity'] = 'Neg'
            elif m2:
                node.lemma = m2.group(1)
                node.feats['Mood'] = 'Int'
            elif m3:
                node.lemma = m3.group(1)
                if node.lemma == '爲':
                    node.lemma = '為'
        elif node.form in self.lemma:
            node.lemma = self.lemma[node.form]
        else:
            node.lemma = node.form
