"""
Block SetTranslation for setting of sentence-level translation (the attribute
text_en for English translation) from a separate text file (one sentence per
line). For example, one can export the original sentences using write.SentencesHtml,
then Google-translate them in the web browser, then CTRL+C CTRL+V to a plain
text editor, save them as translations.txt and import them using this block.

Usage:
udapy -s ud.SetTranslation file=translations.txt < in.conllu > out.conllu

Author: Dan Zeman
"""
from udapi.core.block import Block
import re
import logging

class SetTranslation(Block):
    """
    Set text_en to the next available translation.
    """

    def __init__(self, file, overwrite=False, **kwargs):
        """
        Create the SetTranslation block.

        Parameters:
        file: the name of the text file with the translations (one sentence per line)
        overwrite=1: set the translation even if the sentence already has one
            (default: do not overwrite existing translations)
        """
        super().__init__(**kwargs)
        self.file = file
        fh = open(self.file, 'r', encoding='utf-8')
        self.trlines = fh.readlines()
        self.nlines = len(self.trlines)
        self.iline = 0
        self.overwrite = overwrite

    def process_tree(self, tree):
        if self.iline < self.nlines:
            translation = self.trlines[self.iline]
            self.iline += 1
            comments = []
            if tree.comment:
                comments = tree.comment.split('\n')
            i_tr = -1
            for i in range(len(comments)):
                # The initial '#' character has been stripped.
                if re.match(r'\s*text_en\s*=', comments[i]):
                    i_tr = i
                    break
            if i_tr >= 0:
                if self.overwrite:
                    comments[i_tr] = ' text_en = ' + translation
            else:
                comments.append(' text_en = ' + translation)
            tree.comment = '\n'.join(comments)
        elif self.iline == self.nlines:
            logging.warning('There are only %d translation lines but there are more input sentences.' % self.nlines)
