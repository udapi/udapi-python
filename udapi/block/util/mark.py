"""util.Mark is a special block for marking nodes specified by parameters."""
import re # may be useful in eval, thus pylint: disable=unused-import

from udapi.core.block import Block

# We need eval in this block
# pylint: disable=eval-used
class Mark(Block):
    """Mark nodes specified by parameters.

    Example usage from command line::
    # see non-projective trees with non-projective edges highlighted
    udapy -TM util.Mark node='node.is_nonprojective()' < in | less -R
    """
    def __init__(self, node, mark=1, **kwargs):
        """Create the Mark block object.

        Args:
        `node`: Python expression to be evaluated for each node and if True,
            the node will be marked.

        `mark`: the node will be marked with `Mark=<mark>` in `node.misc`. Default=1.
        """
        super().__init__(**kwargs)
        self.mark = mark
        self.node = node

    def process_node(self, node):
        if eval(self.node):
            node.misc['Mark'] = self.mark
