"""Block ud.ru.FixRemnant ad-hoc fixes

Author: Martin Popel
"""
from udapi.core.block import Block


class FixRemnant(Block):
    """ad-hoc fixing the remaining cases (after ud.Convert1to2) of deprel=remnant in UD_Russian."""

    def process_node(self, node):
        if node.deprel == 'remnant':
            del node.misc['ToDo']
            allnodes = node.root.descendants(add_self=1)
            # train-s1839
            if node.form == 'светлее':
                node.deprel = 'conj'
                for i in (7, 8):
                    allnodes[i].parent = node
            # train-s1316
            elif node.form == '--':
                node.deprel = 'punct'
            elif node.form == 'тонн':
                node.deprel = 'conj'
                node.parent = allnodes[8]
                for i in (9, 12, 13):
                    allnodes[i].parent = node
            # train-s317
            elif node.form == 'Корбюзье':
                node.deprel = 'dep'
                node.parent = allnodes[28]
            elif node.form == 'представителями':
                node.deprel = 'dep'
