#!/usr/bin/env python

import logging
import codecs
import sys

from udapi.core.block import Block


node_attributes = ["ord", "form", "lemma", "upostag", "xpostag", "feats", "head", "deprel", "deps", "misc"]


class Conllu(Block):
    """
    A writer of the Conll-u files.

    """
    def __init__(self, args=None):
        if args is None:
            args = {}

        # File handler
        self.filename = None
        self.file_handler = None
        if 'file_handler' in args:
            self.file_handler = args['file_handler']
            self.filename = self.file_handler.name
        elif 'filename' in args:
            self.filename = args['filename']
            logging.debug('Opening file %s', self.filename)
            self.file_handler = open(self.filename, 'r')
        else:
            logging.warning('No filename specified, using STDOUT.')
            self.file_handler = sys.stdout

        self.file_handler = codecs.getwriter('utf8')(self.file_handler)

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
                # Skip empty sentences (no nodes, just a comment). They are not allowed in CoNLL-U.
                tree_number += 1
                if tree_number > 1:
                    self.file_handler.write("#UDAPI_BUNDLE_CONTINUES\n")

                if root.descendants():
                    # Comments.
                    try:
                        self.file_handler.write(root._aux['comment'])
                    except:
                        pass

                    # Zones.
                    try:
                        self.file_handler.write('#UDAPI_ZONE=' + root.zone()+"\n")
                    except:
                        pass

                    # Nodes.
                    for node in root.descendants():
                        values = [getattr(node, node_attribute) for node_attribute in node_attributes]
                        values[0] = str(values[0])

                        try:
                            values[6] = str(node.parent.ord)
                        except:
                            values[6] = '0'

                        for index in range(0,len(values)):
                            if values[index] == None:
                                values[index] = ''

                        self.file_handler.write('\t'.join([value for value in values]))
                        self.file_handler.write('\n')

                    self.file_handler.write("\n")

                number_of_written_bundles += 1

        logging.info('Wrote %d bundles', number_of_written_bundles)
