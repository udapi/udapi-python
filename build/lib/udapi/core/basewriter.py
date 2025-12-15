"""BaseWriter is the base class for all writer blocks."""
import sys
import logging
import os
from pathlib import Path

import udapi.core.coref
from udapi.core.block import Block
from udapi.core.files import Files


class BaseWriter(Block):
    """Base class for all writer blocks."""

    def __init__(self, files='-', filehandle=None, docname_as_file=False, encoding='utf-8',
                 newline='\n', overwrite=False, path=None, **kwargs):
        super().__init__(**kwargs)
        self.orig_files = files
        self.orig_stdout = sys.stdout
        if filehandle is not None:
            files = None
            self.orig_files = '<filehandle>'
        self.files = Files(filenames=files, filehandle=filehandle)
        self.encoding = encoding
        self.newline = newline
        self.docname_as_file = docname_as_file
        if docname_as_file and files != '-':
            raise ValueError("docname_as_file=1 is not compatible with files=" + files)
        self.overwrite = overwrite
        if overwrite and files != '-':
            raise ValueError("overwrite=1 is not compatible with files=" + files)
        if overwrite and docname_as_file:
            raise ValueError("overwrite=1 is not compatible with docname_as_file=1")
        # interpret path=my_dir/my_subdir as path=my_dir/my_subdir/
        if path and path[-1] != os.sep and '*' not in path:
            path += os.sep
        self.path = path

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
        if document:
            udapi.core.coref.store_coref_to_misc(document)
        if self.orig_files == '<filehandle>':
            logging.info('Writing to filehandle.')
            sys.stdout = self.files.filehandle
            return
        old_filehandle = sys.stdout
        if self.orig_files == '-':
            if self.docname_as_file:
                docname = document.meta.get('docname', None)
                if docname is not None:
                    logging.info('Writing to file %s.', docname)
                    sys.stdout = self._open(docname)
                else:
                    logging.warning('docname_as_file=1 but the document contains no docname')
            elif self.overwrite or self.path:
                docname = document.meta.get('loaded_from', None)
                if docname is not None:
                    if self.path:
                        old_dir, old_filename = os.path.split(docname)
                        new_dir, new_filename = os.path.split(self.path)
                        old_file, old_ext = os.path.splitext(old_filename)
                        new_file, new_ext = os.path.splitext(new_filename)
                        if new_dir in ('', '*'):
                            new_dir = old_dir
                        if new_file in ('', '*'):
                            new_file = old_file
                        if new_ext in ('', '*'):
                            new_ext = old_ext
                        docname = os.path.join(new_dir, new_file + new_ext)
                    logging.info('Writing to file %s.', docname)
                    sys.stdout = self._open(docname)
                else:
                    logging.warning('using overwrite or path but document.meta["loaded_from"] is None')
            else:
                sys.stdout = self.orig_stdout
        else:
            filename = self.next_filename()
            if filename is None:
                raise RuntimeError('There are more documents to save than filenames given (%s)'
                                % self.orig_files)
            elif filename == '-':
                logging.info('Writing to stdout.')
                sys.stdout = self.orig_stdout
            else:
                logging.info('Writing to file %s.', filename)
                sys.stdout = self._open(filename)
        if old_filehandle not in (sys.stdout, self.orig_stdout):
            old_filehandle.close()

    def _open(self, filename):
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        return open(filename, 'wt', encoding=self.encoding, newline=self.newline)

    def after_process_document(self, document):
        sys.stdout.flush()
        if sys.stdout != self.orig_stdout:
            sys.stdout.close()
            sys.stdout = self.orig_stdout
