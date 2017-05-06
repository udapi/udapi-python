"""Block ud.FixRightheaded for making sure flat,fixed,appos,goeswith,list is head initial.

Note that deprel=conj should also be left-headed,
but it is not included in this fix-block by default
because coordinations are more difficult to convert
and one should use a specialized block instead.
"""
from udapi.core.block import Block


class FixRightheaded(Block):
    """Make sure deprel=flat,fixed,... form a head-initial (i.e. left-headed) structure."""

    def __init__(self, deprels='flat,fixed,appos,goeswith,list', **kwargs):
        """Args:
        deprels: comma-separated list of deprels to be fixed.
            Default = flat,fixed,appos,goeswith,list.
        """
        super().__init__(**kwargs)
        self.deprels = deprels.split(',')

    def process_node(self, node):
        for deprel in self.deprels:
            if node.udeprel == deprel and node.precedes(node.parent):
                orig_parent = node.parent
                node.parent = orig_parent.parent
                if deprel != 'conj':
                    for child in orig_parent.children:
                        child.parent = node
                orig_parent.parent = node
                head_deprel = orig_parent.deprel
                orig_parent.deprel = node.deprel
                node.deprel = head_deprel
