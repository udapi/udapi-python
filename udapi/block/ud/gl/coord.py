"""
Block ud.gl.Coord tries to solve some errors in Galician CTG where
coordination is not analyzed correctly.

Author: Dan Zeman
"""
from udapi.core.block import Block

class DeQue(Block):
    """Block for fixing coordination in UD_Galician-CTG."""

    def process_node(self, node):
        # Is this a coordinating conjunction attached to the left?
        if node.udeprel == 'cc' and node.parent.ord < node.ord:
            # Is there a candidate for a right conjunct?
            leftconj = node.parent
            siblings = [x for x in leftconj.siblings(following_only=True)]
            if len(siblings) > 0 and siblings[0].udeprel == leftconj.udeprel:
                rightconj = siblings[0]
                rightconj.parent = leftconj
                rightconj.deprel = 'conj'
                node.parent = rightconj
