"""Sentences class is a reader for plain-text sentences."""
from udapi.core.basereader import BaseReader
from udapi.core.root import Root


class Sentences(BaseReader):
    r"""A reader for plain-text sentences (one sentence per line) files.

    Args:
    ignore_empty_lines: if True, delete empty lines from the input.
        Default=False.
    rstrip: a set of characters to be stripped from the end of each line.
        Default='\r\n '. You can use rstrip='\n' if you want to preserve
        any space or '\r' (Carriage Return) at end of line,
        so that `udpipe.Base` keeps these characters in `SpacesAfter`.
        As most blocks do not expect whitespace other than a space to appear
        in the processed text, using this feature is at your own risk.
    """
    def __init__(self, ignore_empty_lines=False, rstrip='\r\n ', **kwargs):
        self.ignore_empty_lines = ignore_empty_lines
        self.rstrip = rstrip
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
        root.text = line.rstrip(self.rstrip)
        return root
