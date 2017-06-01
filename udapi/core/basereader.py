"""BaseReader is the base class for all reader blocks."""
import re
import logging

from udapi.core.block import Block
from udapi.core.files import Files

# pylint: disable=too-many-instance-attributes


class BaseReader(Block):
    """Base class for all reader blocks."""

    # pylint: disable=too-many-arguments
    def __init__(self, files='-', zone='keep', bundles_per_doc=0, encoding='utf-8',
                 sent_id_filter=None, split_docs=False, ignore_sent_id=False, **kwargs):
        super().__init__(**kwargs)
        self.files = Files(filenames=files)
        self.zone = zone
        self.bundles_per_doc = bundles_per_doc
        self.encoding = encoding
        self._buffer = None
        self.finished = False
        self.sent_id_filter = None
        if sent_id_filter is not None:
            self.sent_id_filter = re.compile(str(sent_id_filter))
            logging.debug('Using sent_id_filter=%s', sent_id_filter)
        self.split_docs = split_docs
        self.ignore_sent_id = ignore_sent_id

    @staticmethod
    def is_multizone_reader():
        """Can this reader read bundles which contain more zones?.

        This implementation returns always True.
        If a subclass supports just one zone in file (e.g. `read.Sentences`),
        this method should be overriden to return False, so `process_document`
        can take advatage of this knowledge and optimize the reading
        (no buffer needed even if `bundles_per_doc` specified).
        """
        return True

    @property
    def filehandle(self):
        """Property with the current file handle."""
        return self.files.filehandle

    @property
    def filename(self):
        """Property with the current filename."""
        return self.files.filename

    @property
    def file_number(self):
        """Property with the current file number (1-based)."""
        return self.files.file_number

    def next_filehandle(self):
        """Go to the next file and retrun its filehandle."""
        return self.files.next_filehandle()

    def read_tree(self, document=None):
        """Load one (more) tree from self.files and return its root.

        This method must be overriden in all readers.
        Usually it is the only method that needs to be implemented.
        The implementation in this base clases raises `NotImplementedError`.
        """
        raise NotImplementedError("Class %s doesn't implement read_tree" % self.__class__.__name__)

    def filtered_read_tree(self, document=None):
        """Load and return one more tree matching the `sent_id_filter`.

        This method uses `read_tree()` internally.
        This is the method called by `process_document`.
        """
        tree = self.read_tree(document)
        if self.sent_id_filter is None:
            return tree
        while True:
            if tree is None:
                return None
            if self.sent_id_filter.match(tree.sent_id) is not None:
                return tree
            logging.debug('Skipping sentence %s as it does not match the sent_id_filter %s.',
                          tree.sent_id, self.sent_id_filter)
            tree = self.read_tree(document)

    # pylint: disable=too-many-branches,too-many-statements
    # Maybe the code could be refactored, but it is speed-critical,
    # so benchmarking is needed because calling extra methods may result in slowdown.
    def process_document(self, document):
        orig_bundles = document.bundles[:]
        last_bundle_id = ''
        bundle = None

        # There may be a tree left in the buffer when reading the last doc.
        if self._buffer:
            # TODO list.pop(0) is inefficient, use collections.deque.popleft()
            bundle = orig_bundles.pop(0) if orig_bundles else document.create_bundle()
            bundle.add_tree(self._buffer)
            if self._buffer.newdoc and self._buffer.newdoc is not True:
                document.meta["docname"] = self._buffer.newdoc
            self._buffer = None

        filehandle = self.filehandle
        if filehandle is None:
            filehandle = self.next_filehandle()
            if filehandle is None:
                self.finished = True
                return

        trees_loaded = 0
        while True:
            root = self.filtered_read_tree(document)
            if root is None:
                if trees_loaded == 0 and self.files.has_next_file():
                    filehandle = self.next_filehandle()
                    continue
                self.finished = not self.files.has_next_file()
                break
            add_to_the_last_bundle = 0
            trees_loaded += 1

            if self.ignore_sent_id:
                root.sent_id = None
            if root.sent_id is not None:
                parts = root.sent_id.split('/', 1)
                bundle_id = parts[0]
                if len(parts) == 2:
                    root.zone = parts[1]
                add_to_the_last_bundle = bundle_id == last_bundle_id
                last_bundle_id = bundle_id

            if self.zone != 'keep':
                root.zone = self.zone

            # The `# newdoc` comment in CoNLL-U marks a start of a new document.
            if root.newdoc:
                if not bundle and root.newdoc is not True:
                    document.meta["docname"] = root.newdoc
                if bundle and self.split_docs:
                    self._buffer = root
                    if orig_bundles:
                        logging.warning("split_docs=1 but the doc had contained %d bundles",
                                        len(orig_bundles))
                    self.finished = False
                    return

            # assign new/next bundle to `bundle` if needed
            if not bundle or not add_to_the_last_bundle:
                if self.bundles_per_doc and bundle and self.bundles_per_doc == bundle.number:
                    self._buffer = root
                    if orig_bundles:
                        logging.warning("bundles_per_doc=%d but the doc had contained %d bundles",
                                        self.bundles_per_doc, len(orig_bundles))
                    return

                if orig_bundles:
                    # TODO list.pop(0) is inefficient, use collections.deque.popleft()
                    bundle = orig_bundles.pop(0)
                    if last_bundle_id and last_bundle_id != bundle.bundle_id:
                        logging.warning('Mismatch in bundle IDs: %s vs %s. Keeping the former one.',
                                        bundle.bundle_id, last_bundle_id)
                else:
                    bundle = document.create_bundle()
                    if last_bundle_id != '':
                        bundle.bundle_id = last_bundle_id

            bundle.add_tree(root)

            # If bundles_per_doc is set and we have read the specified number of bundles,
            # we should end the current document and return.
            # However, if the reader supports reading multiple zones, we can never know
            # if the current bundle has ended or there will be another tree for this bundle.
            # So in case of multizone readers we need to read one extra tree
            # and store it in the buffer (and include it into the next document).
            if self.bundles_per_doc and self.bundles_per_doc == bundle.number \
               and not self.is_multizone_reader():
                return
