import sys
import logging

from udapi.core.block import Block
from udapi.core.files import Files

class BaseWriter(Block):

    def __init__(self, files='-', encoding='utf-8', newline='\n', **kwargs):
        super().__init__(**kwargs)
        self.orig_files = files
        self.files = Files(filenames=files)
        self.encoding = encoding
        self.newline = newline

    def filename(self):
        return self.files.filename()

    def file_number(self):
        return self.files.file_number

    def next_filename(self):
        return self.files.next_filename()

    def before_process_document(self, _):
        if self.orig_files == '-':
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
            logging.debug('Opening stdout.')
            sys.stdout = sys.__stdout__
        else:
            logging.debug('Opening file %s.', filename)
            sys.stdout = open(filename, 'wt', encoding=self.encoding, newline=self.newline)
