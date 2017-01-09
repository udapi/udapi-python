"""Helper class for iterating over filenames."""

import glob
import sys
import os.path
import bz2
import gzip
import lzma

class Files(object):

    def __init__(self, filenames, encoding='utf-8'):
        if type(filenames) is list:
            self.filenames = filenames
        elif type(filenames) is str:
            self.filenames = self.string_to_filenames(filenames)
        else:
            raise ValueError('Parameter "filenames" must be a list or str')
        self.filehandle = None
        self.encoding = encoding
        self.file_number = 0

    def string_to_filenames(self, string):
        # "!" means glob pattern which can contain {dir1,dir2}
        # so it cannot be combined with separating tokens with comma.
        if string[0] == '!':
            pattern = string[1:]
            filenames = glob.glob(pattern)
            if not filenames:
                raise RuntimeError('No filenames matched "%s" pattern' % pattern)
            return filenames
        return [self._token_to_filenames(tok) for tok in string.replace(',', ' ').split()]

    @staticmethod
    def _token_to_filenames(token):
        if token[0] == '!':
            pattern = token[1:]
            filenames = glob.glob(pattern)
            if not filenames:
                raise RuntimeError('No filenames matched "%s" pattern' % pattern)
        elif token[0] == '@':
            filelist_name = sys.stdin if token == '@-' else token[1:]
            with open(filelist_name) as filelist:
                filenames = [line.rstrip('\n') for line in filelist]
            directory = os.path.dirname(token[1:])
            if directory != '.':
                filenames = [f if f[0] != '/' else directory+'/'+f for f in filenames]
        else:
            filenames = token
        return filenames

    def number_of_files(self):
        return len(self.filenames)

    def filename(self):
        if self.file_number == 0 or self.file_number > self.number_of_files():
            return None
        return self.filenames[self.file_number - 1]

    def next_filename(self):
        self.file_number += 1
        return self.filename()

    def has_next_file(self):
        return self.file_number < self.number_of_files()

    def next_filehandle(self):
        filename = self.next_filename()
        if filename is None:
            fhandle = None
        elif filename == '-':
            fhandle = sys.stdin
        else:
            filename_extension = filename.split('.')[-1]
            if filename_extension == 'gz':
                myopen = gzip.open
            elif filename_extension == 'xz':
                myopen = lzma.open
            elif filename_extension == 'bz2':
                myopen = bz2.open
            else:
                myopen = open
            fhandle = myopen(filename, 'rt', encoding=self.encoding)
        self.filehandle = fhandle
        return fhandle
