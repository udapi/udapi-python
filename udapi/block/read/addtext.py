"""read.AddText is a reader for adding word-wrapped plain-text to existing trees."""
from udapi.core.basereader import BaseReader
from udapi.core.root import Root
import logging

class AddText(BaseReader):
    r"""A reader for plain-text files to be stored to existing trees.

    For example LitBank conll files are segmented to sentences and tokenized,
    but the SpacesAfter attributes are missing. We need to load the original
    (raw) texts, which are not tokenized and not segmented, only word-wrapped
    (to 70 characters per line).

    Args:
    add_newpar: add newpar CoNLL-U annotations on empty lines (and the beginning of file)
    """
    def __init__(self, zone='', add_newpar=True, **kwargs):
        super().__init__(zone=zone, **kwargs)
        self.add_newpar = add_newpar

    @staticmethod
    def is_multizone_reader():
        """Can this reader read bundles which contain more zones?.

        This implementation returns always False.
        """
        return False

    def process_document(self, document):
        filehandle = self.next_filehandle()
        if filehandle is None:
            self.finished = True
            return
        text = ''.join(self.filehandle.readlines())
        i, end, was_newpar = 0, len(text), True
        while i <= end and text[i].isspace():
            i += 1

        for bundle in document.bundles:
            root = bundle.get_tree(zone=self.zone)
            if self.add_newpar and was_newpar:
                root.newpar = True
                was_newpar = False
            for node in root.token_descendants:
                if text[i:i+len(node.form)] == node.form:
                    i += len(node.form)
                    if i > end or text[i].isspace():
                        del node.misc['SpaceAfter']
                        was_newpar = i+1 < end and text[i+1] == '\n' and text[i] == '\n'
                        while i <= end and text[i].isspace():
                            i += 1
                    else:
                        node.misc['SpaceAfter'] = 'No'
                        was_newpar = False
                else:
                    logging.warning('Node %s does not match text "%s"', node, text[i:i+20])
                    return
            root.text = root.compute_text()
        self.finished = not self.files.has_next_file()
