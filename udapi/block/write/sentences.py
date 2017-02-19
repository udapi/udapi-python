"""Sentences class is a writer for plain-text sentences."""
from udapi.core.basewriter import BaseWriter


class Sentences(BaseWriter):
    """A writer of plain-text sentences (one per line).

    Usage:
    udapy write.Sentences if_missing=empty < my.conllu > my.txt
    """

    def __init__(self, if_missing='detokenize', **kwargs):
        """Create the Sentences writer block.

        Parameters:
        if_missing: What to do if `root.text` is `None`? (default=detokenize)
         * `detokenize`: use `root.compute_text()` to compute the sentence.
         * `empty`: print an empty line
         * `warn_detokenize`, `warn_empty`: in addition emit a warning via `logging.warning()`
         * `fatal`: raise an exception
        """
        super().__init__(**kwargs)
        self.if_missing = if_missing

    def process_tree(self, tree):
        print(tree.get_sentence(self.if_missing))
