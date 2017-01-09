import re
import logging

from udapi.core.block import Block
from udapi.core.files import Files


class BaseReader(Block):

    def __init__(self, files='-', zone='keep', bundles_per_doc=0, encoding='utf-8',
                 sent_id_filter=None, **kwargs):
        super().__init__(**kwargs)
        self.files = Files(filenames=files)
        self.zone = zone
        self.bundles_per_doc = bundles_per_doc
        self.encoding = encoding
        self._buffer = None
        self.finished = False
        self.sent_id_filter = None
        if sent_id_filter is not None:
            self.sent_id_filter = re.compile(sent_id_filter)
            logging.debug('Using sent_id_filter=%s', sent_id_filter)

    @staticmethod
    def is_multizone_reader():
        return 1

    def filehandle(self):
        return self.files.filehandle

    def filename(self):
        return self.files.filename()

    def file_number(self):
        return self.files.file_number

    def next_filehandle(self):
        return self.files.next_filehandle()

    def read_tree(self, document=None):
        '''Load one (more) tree from self.files and return its root.

        This method must be overriden in all readers.
        Usually it is the only method that needs to be implemented.
        '''
        raise NotImplementedError("Class %s doesn't implement read_tree" % self.__class__.__name__)


    def filtered_read_tree(self, document=None):
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

    def process_document(self, document):
        orig_bundles = document.bundles[:]
        last_bundle_id = ''
        bundle = None

        # There may be a tree left in the buffer when reading the last doc.
        if self._buffer:
            if orig_bundles:
                bundle = orig_bundles.pop(0)  # TODO inefficient, use collections.deque.popleft()
            else:
                bundle = document.create_bundle()
            bundle.add_tree(self._buffer)
            self._buffer = None

        filehandle = self.next_filehandle()
        if filehandle is None:
            self.finished = True
            return

        while True:
            root = self.read_tree(document)
            if root is None:
                self.finished = not self.files.has_next_file()
                break
            add_to_the_last_bundle = 0

            tree_id = root.sent_id
            if tree_id is not None:
                parts = tree_id.split('/', 1)
                bundle_id = parts[0]
                if len(parts)==2:
                    root.zone = parts[1]
                if bundle_id == last_bundle_id:
                    add_to_the_last_bundle = 1
                last_bundle_id = bundle_id
                root.sent_id = None

            if self.zone != 'keep':
                root.zone = self.zone

            # assign new/next bundle to bundle if needed
            if not bundle or not add_to_the_last_bundle:
                if self.bundles_per_doc and bundle and self.bundles_per_doc == bundle.number:
                    self._buffer = root
                    if orig_bundles:
                        logging.warning("bundles_per_doc=%d but the doc had contained %d bundles",
                                        self.bundles_per_doc, len(orig_bundles))
                    return

                if orig_bundles:
                    # TODO inefficient, use collections.deque.popleft()
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
