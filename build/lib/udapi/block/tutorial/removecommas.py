"""tutorial.RemoveCommas helper block."""
from udapi.core.block import Block


class RemoveCommas(Block):
    """Delete all comma nodes and edit SpaceAfter and text accordingly."""

    def process_tree(self, root):
        for node in root.descendants:
            if node.form == ",":
                node.remove(children="rehang")
                del node.prev_node.misc['SpaceAfter']
        root.text = root.compute_text()
