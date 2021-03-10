"""Files is a helper class for iterating over filenames."""

import glob
import io
import sys
import os.path
import bz2
import gzip
import lzma
import itertools


class Files(object):
    """Helper class for iterating over filenames.

    It is used e.g. in ``udapi.core.basereader`` (as `self.files = Files(filenames=pattern)`).
    Constructor takes various arguments:
    >>> files = Files(['file1.txt', 'file2.txt']) # list of filenames or
    >>> files = Files('file1.txt,file2.txt')      # comma- or space-separated filenames in string
    >>> files = Files('file1.txt,file2.txt.gz')   # supports automatic decompression of gz, xz, bz2
    >>> files = Files('@my.filelist !dir??/file*.txt') # @ marks filelist, ! marks wildcard pattern
    The `@filelist` and `!wildcard` conventions are used in several other tools, e.g. 7z or javac.

    Usage:
    >>> while (True):
    >>>     filename = files.next_filename()
            if filename is None:
                break
            ...
    or
    >>> filehandle = files.next_filehandle()
    """

    def __init__(self, filenames=None, filehandle=None, encoding='utf-8'):
        self.filehandle = None
        self.file_number = 0
        self.encoding = encoding
        if filehandle is not None:
            self.filehandle = filehandle
            if filenames is not None:
                raise ValueError('Cannot specify both "filenames" and "filehandle"')
            self.filenames = ['<filehandle_input>']
        elif isinstance(filenames, list):
            self.filenames = filenames
        elif isinstance(filenames, str):
            if filenames == '':
                raise ValueError('Filenames (files=) cannot be an empty string')
            self.filenames = self.string_to_filenames(filenames)
        else:
            raise ValueError('Parameter "filenames" must be a list or str')

    def string_to_filenames(self, string):
        """Parse a pattern string (e.g. '!dir??/file*.txt') and return a list of matching filenames.

        If the string starts with `!` it is interpreted as shell wildcard pattern.
        If it starts with `@` it is interpreted as a filelist with one file per line.
        The string can contain more filenames (or '!' and '@' patterns) separated by spaces
        or commas. For specifying files with spaces or commas in filenames, you need to use
        wildcard patterns or '@' filelist. (But preferably don't use such filenames.)
        """
        # "!" means glob pattern which can contain {dir1,dir2}
        # so it cannot be combined with separating tokens with comma.
        if string[0] == '!':
            pattern = string[1:]
            filenames = glob.glob(pattern)
            if not filenames:
                raise RuntimeError('No filenames matched "%s" pattern' % pattern)
            return filenames
        return list(itertools.chain.from_iterable(self._token_to_filenames(tok)
                                                  for tok in string.replace(',', ' ').split()))

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
                filenames = [f if f[0] != '/' else directory + '/' + f for f in filenames]
        else:
            filenames = [token]
        return filenames

    @property
    def number_of_files(self):
        """Propery with the total number of files."""
        return len(self.filenames)

    @property
    def filename(self):
        """Property with the current file name."""
        if self.file_number == 0 or self.file_number > self.number_of_files:
            return None
        return self.filenames[self.file_number - 1]

    def next_filename(self):
        """Go to the next file and retrun its filename or None (meaning no more files)."""
        self.file_number += 1
        return self.filename

    def has_next_file(self):
        """Is there any other file in the queue after the current one?"""
        return self.file_number < self.number_of_files

    def next_filehandle(self):
        """Go to the next file and retrun its filehandle or None (meaning no more files)."""
        filename = self.next_filename()
        if filename is None:
            fhandle = None
        elif filename == '-':
            fhandle = io.TextIOWrapper(sys.stdin.buffer, encoding=self.encoding)
        elif filename == '<filehandle_input>':
            fhandle = self.filehandle
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
