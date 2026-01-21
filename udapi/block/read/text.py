"""Text class is a reader for word-wrapped plain-text files."""
from udapi.core.basereader import BaseReader
from udapi.core.root import Root


class Text(BaseReader):
    r"""A reader for plain-text files with sentences on one or more lines.
    
    Sentences are separated by one or more empty lines.
    Newlines within sentences are substituted by a space.

    Args:
    rstrip: a set of characters to be stripped from the end of each line.
        Default='\r\n '. You can use rstrip='\n' if you want to preserve
        any space or '\r' (Carriage Return) at end of line,
        so that `udpipe.Base` keeps these characters in `SpacesAfter`.
        As most blocks do not expect whitespace other than a space to appear
        in the processed text, using this feature is at your own risk.
    empty_line: how empty lines are handled. Default 'new_sentence' preserves
        the current behaviour (empty lines mark sentence boundaries). Use
        'keep' to read the entire file content into a single sentence (tree), including
        empty lines. Use 'newpar' to behave like 'new_sentence' but also set
        `root.newpar = True` on each sentence.
    """
    def __init__(self, rstrip='\r\n ', empty_line='new_sentence', **kwargs):
        if empty_line not in {'new_sentence', 'keep', 'newpar'}:
            raise ValueError("empty_line must be 'new_sentence', 'keep' or 'newpar'")
        self.rstrip = rstrip
        self.empty_line = empty_line
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
        if self.empty_line == 'keep':
            content = self.filehandle.read()
            if content == '':
                return None
            root = Root()
            root.text = content
            return root
        lines = []
        line = None
        while True:
            line = self.filehandle.readline()
            # if readline() returns an empty string, the end of the file has been
            # reached, while a blank line is represented by '\n'
            # (or '\r\n' if reading a Windows file on Unix machine).
            if line == '':
                if not lines:
                    return None
                else:
                    break
            elif line in {'\n', '\r\n'}:
                if not lines:
                    continue
                else:
                    break
            else:
                lines.append(line.rstrip(self.rstrip))

        root = Root()
        root.text = " ".join(lines)
        if self.empty_line == 'newpar':
            root.newpar = True
        return root
