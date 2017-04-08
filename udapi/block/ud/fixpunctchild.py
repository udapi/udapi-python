"""Block ud.FixPunctChild for making sure punctuation nodes have no children."""
from udapi.core.block import Block


class FixPunctChild(Block):
    """Make sure punct nodes have no children by rehanging the children upwards."""

    def process_node(self, node):
        while node.parent.deprel == 'punct':
            node.parent = node.parent.parent
