"""util.Split is a special block for splitting documents."""
import math
from udapi.core.basereader import BaseReader

# pylint: disable=abstract-method
# read_tree() does not need to be installed here


class Split(BaseReader):
    """Split Udapi document (with sentence-aligned trees in bundles) into several parts."""

    def __init__(self, parts=None, bundles_per_doc=None, **kwargs):
        """Args:
        parts: into how many parts should the document be split
        bundles_per_doc: number of bundles per the newly created part
        """
        super().__init__(**kwargs)
        if parts is None and bundles_per_doc is None:
            raise ValueError('parts or bundles_per_doc must be specified')
        if parts is not None and bundles_per_doc is not None:
            raise ValueError('Cannot specify both parts and bundles_per_doc')
        self.parts = parts
        self.bundles_per_doc = bundles_per_doc
        self.buffer = None

    @staticmethod
    def is_multizone_reader():
        return False

    def process_document(self, document):
        if not self.buffer:
            self.buffer = document.bundles
            document.bundles = []
            if self.bundles_per_doc is None:
                self.bundles_per_doc = math.ceil(len(self.buffer) / self.parts)
        self.buffer.extend(document.bundles)
        document.bundles = self.buffer[:self.bundles_per_doc]
        self.buffer = self.buffer[self.bundles_per_doc:]
        self.finished = not self.buffer
