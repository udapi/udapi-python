"""Document class is a container for UD trees."""

import io
import contextlib
import logging
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
        self._eid_to_entity = None
        if filename is not None:
            if filename.endswith(".conllu"):
                self.load_conllu(filename, **kwargs)
            elif filename.endswith(".txt"):
                reader = SentencesReader(files=filename, **kwargs)
                reader.apply_on_document(self)
            else:
                raise ValueError("Only *.conllu and *.txt are supported. Provided: " + filename)

    def __iter__(self):
        return iter(self.bundles)

    def __getitem__(self, key):
        return self.bundles[key]

    def __len__(self):
        return len(self.bundles)

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

    def load_conllu(self, filename=None, **kwargs):
        """Load a document from a conllu-formatted file."""
        ConlluReader(files=filename, **kwargs).process_document(self)

    def store_conllu(self, filename):
        """Store a document into a conllu-formatted file."""
        ConlluWriter(files=filename).apply_on_document(self)

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
        """An iterator over all nodes (excluding empty nodes) in the document."""
        for bundle in self:
            for tree in bundle:
                # tree.descendants is slightly slower than tree._descendants,
                # but it seems safer, see the comment in udapi.core.block.Block.process.process_tree().
                for node in tree.descendants:
                    yield node

    @property
    def nodes_and_empty(self):
        """An iterator over all nodes and empty nodes in the document."""
        for bundle in self:
            for tree in bundle:
                for node in tree.descendants_and_empty:
                    yield node

    def draw(self, **kwargs):
        """Pretty print the trees using TextModeTrees."""
        TextModeTrees(**kwargs).run(self)

    def _load_coref(self):
        """De-serialize coreference-related objects (CorefMention, CorefEntity).

        This internal method will be called automatically whenever any coref-related method is called.
        It iterates through all nodes in the document and creates the objects based on the info in MISC
        (stored in attributes Entity, SplitAnte, Bridge).
        """
        if self._eid_to_entity is None:
            udapi.core.coref.load_coref_from_misc(self)

    @property
    def eid_to_entity(self):
        """A dict mapping each eid (entity ID) to a CorefEntity object."""
        self._load_coref()
        return self._eid_to_entity

    @property
    def coref_clusters(self):
        """DEPRECATED: A dict mapping eid to a CorefEntity object.

        Substitute `doc.coref_clusters.values()` and `list(doc.coref_clusters.values())`
        with `doc.coref_entities`.
        Otherwise, substitute `doc.coref_clusters` with `doc.eid_to_entity`.
        """
        logging.warning("coref_clusters is deprecated, use coref_entities or eid_to_entity instead.")
        return self.eid_to_entity

    @property
    def coref_entities(self):
        """A list of all CorefEntity objects in the document."""
        self._load_coref()
        return list(self._eid_to_entity.values())

    @property
    def coref_mentions(self):
        """A sorted list of all CorefMention objects in the document."""
        self._load_coref()
        all_mentions = []
        for entity in self._eid_to_entity.values():
            all_mentions.extend(entity.mentions)
        all_mentions.sort()
        return all_mentions

    def create_coref_entity(self, eid=None, etype=None):
        self._load_coref()
        if not eid:
            counter = 1
            while self._eid_to_entity.get(f'c{counter}'):
                counter += 1
            eid = f'c{counter}'
        elif self._eid_to_entity.get(eid):
            raise ValueError("Entity with eid=%s already exists", eid)
        entity = udapi.core.coref.CorefEntity(eid, etype)
        self._eid_to_entity[eid] = entity
        return entity
