"""Block ud.FixChain for making sure deprel=fixed|goeswith|list does not form a chain."""
from udapi.core.block import Block


class FixChain(Block):
    """Make sure deprel=fixed does not form a chain, but a flat structure."""

    def __init__(self, deprels='fixed,goeswith,list', **kwargs):
        """Args:
        deprels: comma-separated list of deprels to be fixed. Default = fixed,goeswith,list.
        """
        super().__init__(**kwargs)
        self.deprels = deprels.split(',')

    def process_node(self, node):
        for deprel in self.deprels:
            if node.udeprel == deprel and node.parent.udeprel == deprel:
                node.parent = node.parent.parent
