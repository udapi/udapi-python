"""Sentences class is a reader for plain-text sentences."""
from udapi.core.basereader import BaseReader
from udapi.core.root import Root


class Sentences(BaseReader):
    """A reader for plain-text sentences (one sentence per line) files."""

    def read_tree(self, document=None):
        if self.filehandle is None:
            return None
        line = self.filehandle.readline()
        if line == '':
            return None
        root = Root()
        root.text = line.rstrip()
        return root
