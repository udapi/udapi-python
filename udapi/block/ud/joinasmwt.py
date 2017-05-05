"""Block ud.JoinAsMwt for creating multi-word tokens

if multiple neighboring words are not separated by a space
and the boundaries between the word forms are alphabetical.
"""
from udapi.core.block import Block


class JoinAsMwt(Block):
    """Create MWTs if words are not separated by a space.."""

    def process_node(self, node):
        if node.multiword_token:
            return
        mwt_nodes = [node]
        while (node.no_space_after and node.next_node and not node.next_node.multiword_token
               and node.form[-1].isalpha() and node.next_node.form[0].isalpha()):
            node = node.next_node
            mwt_nodes.append(node)
        if len(mwt_nodes) > 1:
            mwt_form = ''.join([n.form for n in mwt_nodes])
            node.root.create_multiword_token(mwt_nodes, mwt_form, node.misc)
