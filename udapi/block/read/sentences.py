"""Sentences class is a reader for plain-text sentences."""
from udapi.core.basereader import BaseReader
from udapi.core.root import Root


class Sentences(BaseReader):
    r"""A reader for plain-text sentences (one sentence per line) files.

    Args:
    ignore_empty_lines: if True, delete empty lines from the input.
        Default=False.
    newdoc_if_empty_line: if True, empty lines mark document boundaries,
        which are marked with `root.newdoc`. Default=False.
    rstrip: a set of characters to be stripped from the end of each line.
        Default='\r\n '. You can use rstrip='\n' if you want to preserve
        any space or '\r' (Carriage Return) at end of line,
        so that `udpipe.Base` keeps these characters in `SpacesAfter`.
        As most blocks do not expect whitespace other than a space to appear
        in the processed text, using this feature is at your own risk.
    """
    def __init__(self, ignore_empty_lines=False, newdoc_if_empty_line=False,
                 rstrip='\r\n ', **kwargs):
        if ignore_empty_lines and newdoc_if_empty_line:
            raise ValueError("ignore_empty_lines is not compatible with newdoc_if_empty_line")
        self.ignore_empty_lines = ignore_empty_lines
        self.newdoc_if_empty_line = newdoc_if_empty_line
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
        preceded_by_empty_line = False
        if self.ignore_empty_lines or self.newdoc_if_empty_line:
            while line in {'\n', '\r\n'}:
                preceded_by_empty_line = True
                line = self.filehandle.readline()
                if line == '':
                    return None
        root = Root()
        root.text = line.rstrip(self.rstrip)
        if self.newdoc_if_empty_line and preceded_by_empty_line:
            root.newdoc = True
        return root

    # The first line in a file also marks a start of new document
    def after_process_document(self, document):
        if self.newdoc_if_empty_line:
            document.bundles[0].trees[0].newdoc = True
