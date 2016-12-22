from udapi.core.block import Block


class RehangPrepositions(Block):

    def process_node(self, node):

        if str(node.upostag) == "ADP":  # TODO: why the hell is str needed

            origparent = node.parent
            node.set_parent(origparent.parent)
            origparent.set_parent(node)
