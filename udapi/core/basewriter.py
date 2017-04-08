"""BaseWriter is the base class for all writer blocks."""
import sys
import logging

from udapi.core.block import Block
from udapi.core.files import Files


class BaseWriter(Block):
    """Base class for all reader blocks."""

    def __init__(self, files='-', docname_as_file=False, encoding='utf-8', newline='\n', **kwargs):
        super().__init__(**kwargs)
        self.orig_files = files
        self.files = Files(filenames=files)
        self.encoding = encoding
        self.newline = newline
        self.docname_as_file = docname_as_file
        if docname_as_file and files != '-':
            raise ValueError("docname_as_file=1 is not compatible with files=" + files)

    @property
    def filename(self):
        """Property with the current filehandle."""
        return self.files.filename

    @property
    def file_number(self):
        """Property with the current file number (1-based)."""
        return self.files.file_number

    def next_filename(self):
        """Go to the next file and retrun its filename."""
        return self.files.next_filename()

    def before_process_document(self, document):
        if self.orig_files == '-':
            if self.docname_as_file:
                docname = document.meta.get('docname', None)
                if docname is not None:
                    logging.info('Writing to file %s.', docname)
                    sys.stdout = open(docname, 'wt', encoding=self.encoding, newline=self.newline)
                else:
                    logging.warning('docname_as_file=1 but the document contains no docname')
            else:
                sys.stdout = sys.__stdout__
            return

        old_filehandle = sys.stdout
        if old_filehandle.fileno != sys.stdout.fileno:
            old_filehandle.close()

        filename = self.next_filename()
        if filename is None:
            raise RuntimeError('There are more documents to save than filenames given (%s)'
                               % self.orig_files)
        elif filename == '-':
            logging.info('Writing to stdout.')
            sys.stdout = sys.__stdout__
        else:
            logging.info('Writing to file %s.', filename)
            sys.stdout = open(filename, 'wt', encoding=self.encoding, newline=self.newline)
