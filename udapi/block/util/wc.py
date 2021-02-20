"""Wc is a special block for printing statistics (word count etc)."""
from udapi.core.block import Block


class Wc(Block):
    """Special block for printing statistics (word count etc)."""

    def __init__(self, tsv=False, **kwargs):
        """Create the Wc block object.

        Params:
        tsv: print just tab-separated-values (trees, words, tokens, MWTs, empty nodes)
        """
        super().__init__(**kwargs)
        self.trees, self.words, self.mwts, self.tokens, self.empty = 0, 0, 0, 0, 0
        self.tsv = tsv

    def process_tree(self, tree):
        self.trees += 1
        self.words += len(tree.descendants)
        mwtoks = len(tree.multiword_tokens)
        self.mwts += mwtoks
        self.tokens += len(tree.token_descendants) if mwtoks else len(tree.descendants)
        self.empty += len(tree.empty_nodes)

    def process_end(self):
        if self.tsv:
            print('\t'.join(map(str, (self.trees, self.words, self.tokens, self.mwts, self.empty))))
        else:
            print('%8d trees\n%8d words' % (self.trees, self.words))
            if self.mwts:
                print('%8d multi-word tokens\n%8d tokens' % (self.mwts, self.tokens))
            if self.empty:
                print('%8d empty nodes' % self.empty)
