"""Block to add missing lemmas in cases where it seems obvious what the lemma should be."""
from udapi.core.block import Block
import logging
import re

class Lemmatize(Block):

    # dictionary: form --> lemma
    lemma = {
        '𡃁仔':   '笭仔',
        '仲':     '重',
        '企':     '徛',
        '係咪':   '係',
        '出嚟':   '出唻',
        '可':     '可以',
        '啦':     '喇',
        '㗎喇':   '㗎嘑',
        '喇':     '嘑',
        '嚟':     '唻',
        '就嚟':   '就唻',
        '死𡃁妹': '死笭妹',
        '老豆':   '老頭',
        '蚊':     '緡',
        '蛋撻':   '蛋澾',
        '返嚟':   '返唻',
        '過嚟人': '過唻人',
        '過嚟':   '過唻'
    }

    def process_node(self, node):
        """
        Parts of the Cantonese treebank lack lemmas. Fortunately, lemmatization
        of Sino-Tibetan languages is pretty straightforward most of the time,
        as the lemma typically equals to the actual word form.

        For Cantonese, lemmatization includes normalization of some characters.
        These are the few cases where lemma differs from the surface form.
        """
        if node.lemma == '' or node.lemma == '_' and node.form != '_' and node.feats['Typo'] != 'Yes':
            if node.form in self.lemma:
                node.lemma = self.lemma[node.form]
            else:
                node.lemma = node.form
