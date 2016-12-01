#!/usr/bin/env python

import logging

from udapi.core.block import Block


def _merge_deprel(deprel):
    """
    Provide a merging of the closely related bags.
    In fact, simply modify deprel name according to (Vulic et al., 2016).

    :param deprel: An original deprel.
    :return: A modified deprel.
    :rtype: str

    """
    if deprel in ['dobj', 'iobj', ]:
        return 'obj'

    if deprel in ['nsubj', 'nsubjpass']:
        return 'subj'

    if deprel in ['xcomp', 'ccomp']:
        return 'comp'

    if deprel in ['advcl', 'advmod']:
        return 'adv'

    return deprel


class Vulic(Block):
    """
    A block for extraction context configurations for training verb representations using word2vecf.

    """

    def __init__(self, args=None):
        """
        Initialization.

        :param args: A dict of optional parameters.

        """
        if args is None:
            args = {}

        self.pool = ['prep', 'acl', 'obj', 'comp', 'adv', 'conj']
        if 'pool' in args:
            self.pool = args['pool'].split(',')

        self.pos = ['VERB']
        if 'pos' in args:
            self.pos = args['pos'].split(',')

        self.suffixed_forms = False
        if 'suffixed_form' in args and args['suffixed_forms'] == '1':
            self.suffixed_forms = True

    def process_node(self, node):
        """
        Extract context configuration for verbs according to (Vulic et al., 2016).

        :param node: A node to be process.

        """
        # We want to extract contexts only for verbs.
        if str(node.upostag) not in self.pos:
            return

        node_form = node.form.lower()
        if self.suffixed_forms:
            node_form = node_form[:-3]

        parent_form = node.parent.form.lower()
        if self.suffixed_forms:
            parent_form = parent_form[:-3]

        # Process node's parent.
        parent_deprel_orig = node.deprel
        parent_deprel_merged = _merge_deprel(parent_deprel_orig)

        if parent_deprel_orig in self.pool:
            print "%s %s_%sI" % (node_form, parent_form, parent_deprel_orig)

        if parent_deprel_orig != parent_deprel_merged and parent_deprel_merged in self.pool:
            print "%s %s_%sI" % (node_form, parent_form, parent_deprel_merged)

        if parent_deprel_orig in self.pool and parent_deprel_orig == 'conj':
            print "%s %s_%s" % (node_form, parent_form, parent_deprel_merged)

        # Process node's children.
        for child in node.children:
            child_deprel_orig = child.deprel
            child_deprel_merged = _merge_deprel(child_deprel_orig)

            child_form = child.form.lower()
            if self.suffixed_forms:
                child_form = child_form[:-3]

            if child_deprel_orig in self.pool:
                print "%s %s_%s" % (node_form, child_form, child_deprel_orig)

            if child_deprel_orig != child_deprel_merged and child_deprel_merged in self.pool:
                print "%s %s_%s" % (node_form, child_form, child_deprel_merged)

            if 'prep' in self.pool:
                has_preposition = False
                for subchild in child.children:
                    if subchild.deprel == 'case':
                        has_preposition = True
                        break

                if has_preposition:
                    print "%s %s_%s" % (node_form, child_form, 'prep')
