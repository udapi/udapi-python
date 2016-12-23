import logging
import sys

from udapi.core.block import Block


class Conllu(Block):
    """
    A writer of files in the CoNLL-U format.

    """

    def __init__(self, args=None):
        if args is None:
            args = {}
        super(Conllu, self).__init__(args)

        # A list of Conllu columns.
        self.node_attributes = ["ord", "form", "lemma", "upostag", "xpostag",
                                "raw_feats", "head", "deprel", "raw_deps", "misc"]

        # File handler
        self.filename = None
        self.file_handler = None
        if 'file_handler' in args:
            self.file_handler = args['file_handler']
            self.filename = self.file_handler.name
        elif 'filename' in args:
            self.filename = args['filename']
            logging.debug('Opening file %s', self.filename)
            # CoNLL-U specification requires utf8 and \n newlines even on Windows (\r\n is forbidden).
            # Python3 uses os.linesep by default, so we need to override it
            # with newline='\n'.
            self.file_handler = open(
                self.filename, 'wt', encoding='utf-8', newline='\n')
        else:
            logging.warning('No filename specified, using STDOUT.')
            self.file_handler = sys.stdout

    def process_document(self, document):
        """
        FIXME

        :param document:
        :return:
        """
        number_of_written_bundles = 0
        for bundle in document.bundles:
            if (number_of_written_bundles % 1000) == 0:
                logging.info('Wrote %d bundles', number_of_written_bundles)

            tree_number = 0
            for root in bundle:
                tree_number += 1
                if tree_number > 1:
                    self.file_handler.write("#UDAPI_BUNDLE_CONTINUES\n")

                # Skip empty sentences (no nodes, just a comment). They are not
                # allowed in CoNLL-U.
                if root.descendants():
                    # Comments.
                    try:
                        self.file_handler.write(root._aux['comment'])
                    except:
                        pass

                    # Zones.
                    try:
                        self.file_handler.write(
                            '#UDAPI_ZONE=' + root.zone() + "\n")
                    except:
                        pass

                    # Nodes.
                    for node in root.descendants():
                        values = [getattr(node, node_attribute)
                                  for node_attribute in self.node_attributes]
                        values[0] = str(values[0])

                        try:
                            values[6] = str(node.parent.ord)
                        except:
                            values[6] = '0'

                        for index in range(0, len(values)):
                            if values[index] is None:
                                values[index] = ''

                        self.file_handler.write(
                            '\t'.join([value for value in values]))
                        self.file_handler.write('\n')

                    # Each tree in CoNLL-U (including the last tree in a file)
                    # must end with an empty line.
                    self.file_handler.write('\n')

                number_of_written_bundles += 1

        logging.info('Wrote %d bundles', number_of_written_bundles)
