"""Document class is a container for UD trees."""

import io
import contextlib
import udapi.core.coref
from udapi.core.bundle import Bundle
from udapi.block.read.conllu import Conllu as ConlluReader
from udapi.block.write.conllu import Conllu as ConlluWriter
from udapi.block.read.sentences import Sentences as SentencesReader
from udapi.block.write.textmodetrees import TextModeTrees

class Document(object):
    """Document is a container for Universal Dependency trees."""

    def __init__(self, filename=None, **kwargs):
        """Create a new Udapi document.

        Args:
        filename: load the specified file.
            Only `*.conlu` (using `udapi.block.read.conllu`)
            and `*.txt` (using `udapi.block.read.sentences`) filenames are supported.
            No pre-processing is applied, so when loading the document from a *.txt file,
            `Document("a.txt").nodes` will be empty and you need to run tokenization first.
            You can pass additional parameters for `udapi.block.read.sentences`
            (`ignore_empty_lines` and `rstrip`).
        """
        self.bundles = []
        self._highest_bundle_id = 0
        self.meta = {}
        self.json = {}
        self._coref_clusters = None
        if filename is not None:
            if filename.endswith(".conllu"):
                self.load_conllu(filename)
            elif filename.endswith(".txt"):
                reader = SentencesReader(files=filename, **kwargs)
                reader.apply_on_document(self)
            else:
                raise ValueError("Only *.conllu and *.txt are supported. Provided: " + filename)

    def __iter__(self):
        return iter(self.bundles)

    def __getitem__(self, key):
        return self.bundles[key]

    def __str__(self):
        """Pretty print the whole document using write.TextModeTrees."""
        fh = io.StringIO()
        with contextlib.redirect_stdout(fh):
            TextModeTrees(color=True).run(self)
        return fh.getvalue()

    def create_bundle(self):
        """Create a new bundle and add it at the end of the document."""
        self._highest_bundle_id += 1
        bundle = Bundle(document=self, bundle_id=str(self._highest_bundle_id))
        self.bundles.append(bundle)
        bundle.number = len(self.bundles)
        return bundle

    def load_conllu(self, filename=None):
        """Load a document from a conllu-formatted file."""
        reader = ConlluReader(files=filename)
        reader.apply_on_document(self)

    def store_conllu(self, filename):
        """Store a document into a conllu-formatted file."""
        writer = ConlluWriter(files=filename)
        writer.apply_on_document(self)

    def from_conllu_string(self, string):
        """Load a document from a conllu-formatted string."""
        reader = ConlluReader(filehandle=io.StringIO(string))
        reader.apply_on_document(self)

    def to_conllu_string(self):
        """Return the document as a conllu-formatted string."""
        fh = io.StringIO()
        with contextlib.redirect_stdout(fh):
            ConlluWriter().apply_on_document(self)
        return fh.getvalue()

    @property
    def trees(self):
        """An iterator over all trees in the document."""
        for bundle in self:
            for tree in bundle:
                yield tree

    @property
    def nodes(self):
        """An iterator over all nodes in the document."""
        for bundle in self:
            for tree in bundle:
                for node in tree.descendants:
                    yield node

    def draw(self, **kwargs):
        """Pretty print the trees using TextModeTrees."""
        TextModeTrees(**kwargs).run(self)

    def _load_coref(self):
        """De-serialize coreference-related objects (CorefMention, CorefCluster).

        This internal method will be called automatically whenever any coref-related method is called.
        It iterates through all nodes in the document and creates the objects based on the info in MISC
        (stored in attributes ClusterId, MentionSpan, ClusterType, Split, Bridging).
        """
        if self._coref_clusters is None:
            udapi.core.coref.load_coref_from_misc(self)

    @property
    def coref_clusters(self):
        """A dict mapping ClusterId to a CorefCluster object."""
        self._load_coref()
        return self._coref_clusters
