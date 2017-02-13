"""Sentences class is a reader for plain-text sentences."""
from udapi.core.basereader import BaseReader
from udapi.core.root import Root


class Sentences(BaseReader):
    """A reader for plain-text sentences (one sentence per line) files."""

    @staticmethod
    def is_multizone_reader():
        """Can this reader read bundles which contain more zones?.

        This implementation returns always False.
        """
        return False

    def read_tree(self, document=None):
        if self.filehandle is None:
            return None
        line = self.filehandle.readline()
        if line == '':
            return None
        root = Root()
        root.text = line.rstrip()
        return root
