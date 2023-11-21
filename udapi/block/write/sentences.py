"""Sentences class is a writer for plain-text sentences."""
from udapi.core.basewriter import BaseWriter


class Sentences(BaseWriter):
    """A writer of plain-text sentences (one sentence per line).

    Usage:
    udapy write.Sentences if_missing=empty < my.conllu > my.txt
    udapy write.Sentences newdoc=1 newpar=1 < my.conllu > my.txt
    """

    def __init__(self, if_missing='detokenize', newdoc=None, newpar=None, **kwargs):
        """Create the Sentences writer block.

        Parameters:
        if_missing: What to do if `root.text` is `None`? (default=detokenize)
         * `detokenize`: use `root.compute_text()` to compute the sentence.
         * `empty`: print an empty line
         * `warn_detokenize`, `warn_empty`: in addition emit a warning via `logging.warning()`
         * `fatal`: raise an exception
        newdoc: What to do if `root.newdoc` is not None? (default=None)
         * None: ignore it
         * True: print an empty_line (except for the first tree, i.e. bundle.number==1)
        newpar: What to do if `root.newpar` is not None? (default=None)
         * None: ignore it
         * True: print an empty_line (except for the first tree, i.e. bundle.number==1)
        """
        super().__init__(**kwargs)
        self.if_missing = if_missing
        self.newdoc = newdoc
        self.newpar = newpar

    def process_tree(self, tree):
        if self.newdoc and tree.newdoc and tree.bundle.number > 1:
            print()
        if self.newpar and tree.newpar and tree.bundle.number > 1:
            print()
        print(tree.get_sentence(self.if_missing))
