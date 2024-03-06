"""util.Mark is a special block for marking nodes specified by parameters."""
import re  # may be useful in eval, thus pylint: disable=unused-import

from udapi.core.block import Block

# We need eval in this block
# pylint: disable=eval-used


class Mark(Block):
    """Mark nodes specified by parameters.

    Example usage from command line::
    # see non-projective trees with non-projective edges highlighted
    udapy -TM util.Mark node='node.is_nonprojective()' < in | less -R
    """

    def __init__(self, node, mark=1, mark_attr="Mark", add=True, print_stats=False, empty=False, **kwargs):
        """Create the Mark block object.

        Args:
        `node`: Python expression to be evaluated for each node and if True,
            the node will be marked.

        `mark`: the node will be marked with `Mark=<mark>` in `node.misc`. Default=1.

        `mark_attr`: use this MISC attribute name instead of "Mark".

        `add`: should we keep existing Mark|ToDo|Bug? Default=True.

        `print_stats`: print the total number of marked nodes to stdout at process_end

        `empty`: apply the code also on empty nodes
        """
        super().__init__(**kwargs)
        self.mark = mark
        self.mark_attr = mark_attr
        self.node = node
        self.add = add
        self.print_stats = print_stats
        self._marked = 0
        self.empty = empty

    def process_node(self, node):
        if eval(self.node):
            node.misc[self.mark_attr] = self.mark
            self._marked += 1
        elif not self.add:
            del node.misc[self.mark_attr]
            del node.misc['ToDo']
            del node.misc['Bug']

    def process_empty_node(self, empty_node):
        if self.empty:
            self.process_node(empty_node)

    def process_end(self):
        if self.print_stats:
            print(f'util.Mark marked {self._marked} nodes')
