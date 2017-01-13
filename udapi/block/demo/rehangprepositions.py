from udapi.core.block import Block


class RehangPrepositions(Block):

    def process_node(self, node):
        if node.upos == "ADP":
            origparent = node.parent
            node.parent = origparent.parent
            origparent.parent = node
