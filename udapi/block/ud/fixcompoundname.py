"""
Block ud.FixCompoundName finds compound relations between PROPN nodes and converts
them to flat:name. This is not necessarily correct in all situations. The difference
between compound and flat is that compound allows to distinguish head and modifier.
Multiword person names (given name and surname, or various other patterns) typically
should be analyzed as flat but there are treebanks that incorrectly use compound
for person names. This block can be used to fix them.
"""
from udapi.core.block import Block
import regex as re
import logging


class FixCompoundName(Block):
    """
    Converts a compound relation between two PROPN nodes into a flat relation.
    Compounds of a PROPN and a non-PROPN will be left alone, although they are
    suspicious, too.
    """

    def process_node(self, node):
        if node.upos == 'PROPN' and node.udeprel == 'compound' and node.parent.upos == 'PROPN':
            origparent = node.parent
            grandparent = origparent.parent
            outdeprel = origparent.deprel
            # See if there are other PROPN compound siblings.
            # (The list node.children is automatically sorted by ord. If any new sorting is needed later, we can compare nodes directly, their default comparison value is ord.)
            namewords = [x for x in origparent.children(add_self=True) if x.upos == 'PROPN' and (x.udeprel == 'compound' or x == origparent)]
            # The Hindi treebank tags dates (['30', 'navaṁbara'], ['disaṁbara', '1993']) as PROPN compounds.
            # This is wrong but it is also different from personal names we are targeting here.
            # Hence, we will skip "names" that contain numbers.
            if any(re.search(r"\d", x.form) for x in namewords):
                #logging.info(str([x.misc['Translit'] for x in namewords]))
                ###!!! We currently cannot transform enhanced dependencies.
                ###!!! If we proceed, the basic tree would diverge from the enhanced dependencies.
                if len(node.deps) > 0:
                    logging.fatal('There are enhanced dependencies but ud.FixCompoundName has been implemented only for basic dependencies.')
                # The first name word will be the technical head. If it is the current parent, fine.
                head = namewords[0]
                rest = namewords[1:]
                if head != origparent:
                    head.parent = grandparent
                    head.deprel = outdeprel
                for n in rest:
                    n.parent = head
                    n.deprel = 'flat:name'
