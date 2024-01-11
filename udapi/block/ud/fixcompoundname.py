"""
Block ud.FixCompoundName finds compound relations between PROPN nodes and converts
them to flat:name. This is not necessarily correct in all situations. The difference
between compound and flat is that compound allows to distinguish head and modifier.
Multiword person names (given name and surname, or various other patterns) typically
should be analyzed as flat but there are treebanks that incorrectly use compound
for person names. This block can be used to fix them.
"""
from udapi.core.block import Block
import logging


class FixCompoundName(Block):
    """
    Converts a compound relation between two PROPN nodes into a flat relation.
    Compounds of a PROPN and a non-PROPN will be left alone, although they are
    suspicious, too.
    """

    def process_node(self, node):
        if node.upos == 'PROPN' and node.udeprel == 'compound' and node.parent.upos == 'PROPN':
            # See if there are other PROPN compound siblings.
            namewords = [x for x in node.siblings if x.upos == 'PROPN' and x.udeprel == 'compound']
            namewords.append(node.parent)
            namewords = sorted(namewords, key=lambda x: x.ord)
            ###!!! We currently cannot transform enhanced dependencies.
            ###!!! If we proceed, the basic tree would diverge from the enhanced dependencies.
            if len(node.deps) > 0:
                logging.fatal('There are enhanced dependencies but ud.FixCompoundName has been implemented only for basic dependencies.')
            # The first name word will be the technical head. If it is the current parent, fine.
            if namewords[0] != node.parent:
                namewords[0].parent = node.parent.parent
                namewords[0].deprel = node.parent.deprel
            for i in range(len(namewords)-1):
                namewords[i+1].parent = namewords[0]
                namewords[i+1].deprel = 'flat:name'
