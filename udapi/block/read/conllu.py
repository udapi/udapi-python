import logging
import re
import bz2

from udapi.core.basereader import BaseReader
from udapi.core.root import Root


class Conllu(BaseReader):
    """
    A reader of the Conll-u files.

    """
    def __init__(self, args=None):
        if args is None:
            args = {}

        super(BaseReader, self).__init__()

        # A list of Conllu columns.
        self.node_attributes = ["ord", "form", "lemma", "upostag", "xpostag",
                                "feats", "head", "deprel", "deps", "misc"]

        # TODO: this should be invoked from the parent class
        self.finished = False

        # Strict.
        self.strict = False
        if 'strict' in args and args['strict'] in [True, 1, '1', 'True', 'true']:
            self.strict = True

        # ID filter.
        self.sentence_id_filter = None
        if 'sentence_id_filter' in args:
            self.sentence_id_filter = re.compile(args['sentence_id_filter'])

        # Bundles per document.
        self.bundles_per_document = float("inf")
        if 'bundles_per_document' in args:
            self.bundles_per_document = int(args['bundles_per_document'])

        # File handler
        self.filename = None
        self.file_handler = None
        if 'file_handler' in args:
            self.file_handler = args['file_handler']
            self.filename = self.file_handler.name
        elif 'filename' in args:
            self.filename = args['filename']
            filename_extension = self.filename.split('.')[-1]

            # Use bz2 lib when bz2 file is given.
            if filename_extension == 'bz2':
                logging.info('Opening BZ2 file %s', self.filename)
                self.file_handler = bz2.open(self.filename, 'rt', encoding='utf-8')
            else:
                logging.info('Opening regular file %s', self.filename)
                self.file_handler = open(self.filename, 'rt', encoding='utf-8')
        else:
            raise ValueError('No file to process')

        # Remember total number of bundles
        self.total_number_of_bundles = 0

    def _get_next_raw_bundle(self):
        """
        Read lines for one bundle from the self.file_handler.
        Bundles are separated by an empty line.

        :return: A list of lines that represent one bundle.
        :rtype: list

        """
        lines = []
        for line in self.file_handler:
            line = line.rstrip()
            if line == '':
                break

            lines.append(line)

        return lines

    def process_document(self, document):
        logging.info('Attributes = %r', self.node_attributes)

        number_of_processed_bundles = -1
        number_of_loaded_bundles = 0

        # Compile a set of regular expressions that will be searched over the lines.
        re_comment_like = re.compile(r'^#')
        re_sentence_id = re.compile(r'^# sent_id (\S+)')
        re_multiword_tokens = re.compile(r'^\d+-')

        # While there are some raw bundles, we process them.
        while 42:
            if number_of_loaded_bundles > 0 and (number_of_loaded_bundles % 1000) == 0:
                logging.info('Processed %7d bundles. Loaded %7d bundles (%7d in total)',
                             number_of_processed_bundles, number_of_loaded_bundles, self.total_number_of_bundles)

            # If we can not add next bundle, return document.
            if number_of_loaded_bundles >= self.bundles_per_document:
                logging.debug('Reached number of requested bundles (%d)', self.bundles_per_document)
                return document

            # Obtain a raw bundle.
            raw_bundle = self._get_next_raw_bundle()
            number_of_processed_bundles += 1

            if len(raw_bundle) == 0:
                logging.debug('No next bundle to process')
                break

            # Check if all lines have correct number of data fields.
            # Skip invalid bundle otherwise.
            if self.strict:
                raw_bundle_check = True
                for line in raw_bundle:
                    if re_comment_like.search(line) is not None:
                        continue
                    if len(line.split('\t')) != len(self.node_attributes):
                        raw_bundle_check = False

                if not raw_bundle_check:
                    raise RuntimeError('Detected an invalid bundle: %r' % raw_bundle)

            # Initialize the data structures.
            root_node = Root()
            nodes = [root_node]
            comments = []

            # Try to process a raw bundle.
            try:
                # Process lines.
                for (n_line, line) in enumerate(raw_bundle):
                    logging.debug('Processing line %r', line)

                    # Sentence identifier.
                    match = re_sentence_id.search(line)
                    if match is not None:
                        sent_id = match.group(1)
                        logging.debug('Matched sent_id keyword with value %s', sent_id)
                        root_node.sent_id = sent_id
                        continue

                    # Comments.
                    match = re_comment_like.search(line)
                    if match is not None:
                        comments.append(line[1:])
                        continue

                    # FIXME Multi-word tokens are temporarily avoided.
                    if re_multiword_tokens.search(line):
                        logging.debug('Skipping multi-word tokens %s', line)
                        continue

                    # Otherwise the line is a tab-separated list of node attributes.
                    node = root_node.create_child()
                    raw_node_attributes = line.split('\t')
                    for (n_attribute, attribute_name) in enumerate(self.node_attributes):
                        if attribute_name == 'feats':
                            attribute_name = 'raw_feats'
                        if attribute_name == 'deps':
                            attribute_name = 'raw_deps'
                        setattr(node, attribute_name, raw_node_attributes[n_attribute])

                    nodes.append(node)

                    # TODO: kde se v tomhle sloupecku berou podtrzitka
                    try:
                        node.head = int(node.head)
                    except ValueError:
                        node.head = 0

                    # TODO: poresit multitokeny
                    try:
                        node.ord = int(node.ord)
                    except ValueError:
                        pass

                # At least one node should be parsed.
                if len(nodes) == 0:
                    raise ValueError('Probably two empty lines following each other.')

                # If specified, check sentence ID to match the sentence ID filter.
                if self.sentence_id_filter is not None:
                    if self.sentence_id_filter.match(root_node.sent_id) is None:
                        logging.debug('Skipping sentence %s as it does not match the sentence ID filter.',
                                      root_node.sent_id)
                        continue

                # Set parents for each node.
                nodes[0].aux['comments'] = '\n'.join(comments)
                nodes[0].aux['descendants'] = nodes[1:]
                for node in nodes[1:]:
                    node.parent = nodes[node.head]

                # Create a new bundle with a new root node.
                bundle = document.create_bundle()
                bundle.add_tree(root_node)
            except Exception as exception:
                if self.strict:
                    raise RuntimeError('An exception occurred at bundle %d (%s): %s.' % (number_of_processed_bundles,
                                                                                         root_node.sent_id, exception))
                else:
                    logging.warning('An exception occurred at bundle %d (%s): %r. Skipping this bundle.',
                                    number_of_processed_bundles, root_node.sent_id, exception)
                    continue

            number_of_loaded_bundles += 1
            self.total_number_of_bundles += 1

        logging.info('Processed %7d bundles. Loaded %7d bundles.', number_of_processed_bundles,
                     number_of_loaded_bundles)

        self.finished = True
        return document
