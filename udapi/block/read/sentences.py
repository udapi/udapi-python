"""Sentences class is a reader for plain-text sentences."""
from udapi.core.basereader import BaseReader
from udapi.core.root import Root


class Sentences(BaseReader):
    """A reader for plain-text sentences (one sentence per line) files."""

    def __init__(self, ignore_empty_lines=False, **kwargs):
        self.ignore_empty_lines = ignore_empty_lines
        super().__init__(**kwargs)

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
        # if readline() returns an empty string, the end of the file has been
        # reached, while a blank line is represented by '\n'
        # (or '\r\n' if reading a Windows file on Unix machine).
        if line == '':
            return None
        if self.ignore_empty_lines:
            while line in {'\n', '\r\n'}:
                line = self.filehandle.readline()
                if line == '':
                    return None
        root = Root()
        root.text = line.rstrip()
        return root
