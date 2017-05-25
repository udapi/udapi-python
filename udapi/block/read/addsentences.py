"""AddSentences class is a reader for adding plain-text sentences."""
from udapi.core.basereader import BaseReader

# pylint: disable=abstract-method
# read_tree() does not need to be implemented here


class AddSentences(BaseReader):
    """A reader for adding plain-text sentences (one sentence per line) files.

    The sentences are added to an existing trees.
    This is useful, e.g. if there are the original raw texts in a separate file:

    `cat in.conllu | udapy -s read.Conllu read.AddSentences files=in.txt > merged.conllu`
    """

    def __init__(self, zone='', into='text', **kwargs):
        """Args:
        into: name of the comment-attribute where the sentence should be stored. Default = text.
            That is the sentence is stored in `root.text` and in CoNLL-U it will look like e.g.
            `# text = John loves Mary.`
            Any other name than "text" is stored to `root.comment`, so e.g. `into=english_text`
            will result in a CoNLL-U with a comment line:
            `# english_text = John loves Mary.`
        """
        super().__init__(zone=zone, **kwargs)
        self.into = into

    @staticmethod
    def is_multizone_reader():
        """Can this reader read bundles which contain more zones?.

        This implementation returns always False.
        """
        return False

    def process_document(self, document):
        filehandle = self.filehandle
        if filehandle is None:
            filehandle = self.next_filehandle()
            if filehandle is None:
                self.finished = True
                return

        for bundle in document.bundles:
            line = self.filehandle.readline()
            if line == '':
                raise IOError('File does not have enough lines')
            root = bundle.get_tree(zone=self.zone)
            if self.into == 'text':
                root.text = line.rstrip()
            else:
                root.comment += ' ' + self.into + " = " + line.rstrip() + "\n"
        self.finished = not self.files.has_next_file()
