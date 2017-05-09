"""transform.Flatten block for flattening trees."""
from udapi.core.block import Block

class Flatten(Block):
    """Apply `node.parent = node.root; node.deprel = 'root'` on all nodes."""

    def process_node(self, node):
        node.parent = node.root
        node.deprel = 'root'
