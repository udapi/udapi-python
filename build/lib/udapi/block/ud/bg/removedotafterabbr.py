"""Block ud.bg.RemoveDotAfterAbbr deletes extra PUNCT nodes after abbreviations.

Usage:
udapy -s ud.bg.RemoveDotAfterAbbr < in.conllu > fixed.conllu

Author: Martin Popel
"""
from udapi.core.block import Block


class RemoveDotAfterAbbr(Block):
    """Block for deleting extra PUNCT nodes after abbreviations.

    If an abrreviation is followed by end-sentence period, most languages allow just one period.
    However, in some treebanks (e.g. UD_Bulgarian v1.4) two periods are annotated::
    # text = 1948 г.
    1  1948  1948  ADJ
    2  г.    г.    NOUN
    3  .     .     PUNCT

    The problem is that the `text` comment does not match with the word forms.
    In https://github.com/UniversalDependencies/docs/issues/410 it was decided that the least-wrong
    solution (and most common in other treebanks) is to delete the end-sentence punctuation::
    # text = 1948 г.
    1  1948  1948  ADJ
    2  г.    г.    NOUN

    This block is not specific for Bulgarian, just that UD_Bulgarian is probably the only treebank
    where this transformation is needed.
    """

    def process_tree(self, root):
        nodes = root.descendants
        if len(nodes) > 1 and nodes[-1].form == '.' and nodes[-2].form.endswith('.') and root.text:
            if not (root.text.endswith('..') or root.text.endswith('. .')):
                nodes[-1].remove(children='rehang_warn')
