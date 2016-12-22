import logging
import sys

from udapi.core.block import Block


# TODO
# Implement parameters, colors and nonprojectivities according to the Perl implementation
# https://github.com/udapi/udapi-perl/blob/master/lib/Udapi/Block/Write/TextModeTrees.pm

def get_number_of_antecedents(node):
    """
    Return a number of antecedents.

    :param node: An input node.
    :return: A number of antecedents.
    :rtype: int

    """
    n_antecedents = 0
    while node.parent.ord != 0:
        n_antecedents += 1
        node = node.parent

    return n_antecedents


def print_tree(root_node):
    """
    Print pretty ASCII dependency tree to the standard output.

    :param root_node:

    """
    basic_offset = 29
    for node in root_node.descendants():
        # logging.info(' ')
        # logging.info('Processing node %d', node.ord)

        # Format offset arcs.
        offset = ''
        current_node = node
        while not current_node.parent.is_root():
            # logging.info('Current node = %d', current_node.ord)

            if current_node.ord == node.ord:
                # logging.info('- node first offset')
                offset = ' ' * basic_offset
                current_node = current_node.parent
                continue

            if current_node.ord > current_node.parent.ord:
                # logging.info('- adding arc')
                offset = '|' + ' ' * (basic_offset - 1) + offset
            else:
                # logging.info('- do not adding arc')
                offset = ' ' * basic_offset + offset

            current_node = current_node.parent

        # Format deprel label.
        deprel = '%10s' % node.deprel
        deprel = deprel.replace(' ', '-')

        subtree = ''
        if len(node.children) > 0:
            subtree = '--+'

        if 0 < node.parent.ord < node.ord:
            print('     %s|' % offset)

        print('%2d : %s+--%10s--[%10s]%s' % (node.ord, offset, deprel, node.form[:-3][:10], subtree))

        if 0 < node.parent.ord > node.ord:
            print('     %s|' % offset)


class TextModeTrees(Block):
    """
    A pretty ACSII printer of the dependency trees.

    """
    def __init__(self, args=None):
        super(TextModeTrees, self).__init__(args)
        if args is None:
            args = {}

    def process_document(self, document):
        """
        Print pretty ASCII dependency tree to the standard output.

        :param document: An input document.

        """
        number_of_written_bundles = 0
        for bundle in document.bundles:
            if (number_of_written_bundles % 1000) == 0:
                logging.info('Wrote %d bundles', number_of_written_bundles)

            for root in bundle:
                print_tree(root)

        logging.info('Wrote %d bundles', number_of_written_bundles)
