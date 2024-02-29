"""transform.Flatten block for flattening trees."""
from udapi.core.block import Block

class Flatten(Block):
    """Apply `node.parent = node.root; node.deprel = 'root'` on all nodes."""

    def __init__(self, oneroot=False, **kwargs):
        """Args:
        oneroot: only the first node will have deprel 'root'.
            All other nodes will depend on the first node with deprel 'dep'.
            This option makes the trees valid according to the validator.
            (default=False)
        """
        super().__init__(**kwargs)
        self.oneroot = oneroot

    def process_tree(self, tree):
        for node in tree.descendants:
            node.parent = node.root
            node.deprel = 'root'
        if self.oneroot:
            first = tree.descendants[0]
            for node in tree.descendants[1:]:
                node.parent = first
                node.deprel = 'dep'
