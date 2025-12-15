"""RehangPrepositions demo block."""
from udapi.core.block import Block


class RehangPrepositions(Block):
    """This block takes all prepositions (upos=ADP) and rehangs them above their parent."""

    def process_node(self, node):
        if node.upos == "ADP":
            origparent = node.parent
            node.parent = origparent.parent
            origparent.parent = node
