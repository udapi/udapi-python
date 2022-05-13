"""Block to fix annotation of то есть in Russian."""
from udapi.core.block import Block
import logging
import re

class FixToEst(Block):

    def process_node(self, node):
        """
        In the converted data from Kira, the fixed expression "то есть" ("that is")
        is treated as a subordinator and attached as "mark", which later makes it
        part of complex enhanced relation labels. I believe that this analysis is
        wrong and that it will be better to label these expressions as "cc".
        """
        if node.udeprel == 'mark' and node.lemma == 'то':
            if len([c for c in node.children if c.udeprel == 'fixed' and c.lemma == 'быть']) > 0:
                self.set_basic_and_enhanced(node, node.parent, 'cc', 'cc')

    def set_basic_and_enhanced(self, node, parent, deprel, edeprel):
        '''
        Modifies the incoming relation of a node both in the basic tree and in
        the enhanced graph. If the node does not yet depend in the enhanced
        graph on the current basic parent, the new relation will be added without
        removing any old one. If the node already depends multiple times on the
        current basic parent in the enhanced graph, all such enhanced relations
        will be removed before adding the new one.
        '''
        old_parent = node.parent
        node.parent = parent
        node.deprel = deprel
        node.deps = [x for x in node.deps if x['parent'] != old_parent]
        new_edep = {}
        new_edep['parent'] = parent
        new_edep['deprel'] = edeprel
        node.deps.append(new_edep)
