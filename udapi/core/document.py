"""Document class is a container for UD trees."""

from udapi.core.bundle import Bundle

from udapi.block.read.conllu import Conllu as ConlluReader
from udapi.block.write.conllu import Conllu as ConlluWriter


class Document(object):
    """Document is a container for Universal Dependency trees."""

    def __init__(self):
        self.bundles = []
        self._highest_bundle_id = 0
        self.meta = {}
        self.json = {}

    def __iter__(self):
        return iter(self.bundles)

    def create_bundle(self):
        """Create a new bundle and add it at the end of the document."""
        self._highest_bundle_id += 1
        bundle = Bundle(document=self, bundle_id=str(self._highest_bundle_id))
        self.bundles.append(bundle)
        bundle.number = len(self.bundles)
        return bundle

    def load_conllu(self, filename):
        """Load a document from a conllu-formatted file."""
        reader = ConlluReader(files=filename)
        reader.process_document(self)

    def store_conllu(self, filename):
        """Store a document into a conllu-formatted file."""
        writer = ConlluWriter(files=filename)
        writer.process_document(self)
