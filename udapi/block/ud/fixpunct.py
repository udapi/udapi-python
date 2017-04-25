"""Block ud.FixPunct for making sure punctuation is attached projectively.

Punctuation in Universal Dependencies has the tag PUNCT, dependency relation punct,
and is always attached projectively, usually to the head of a neighboring subtree
to its left or right.
Punctuation normally does not have children. If it does, we will skip it.
It is unclear what to do anyway, and we won't have to check for cycles.

Tries to re-attach punctuation projectively.
It should help in cases where punctuation is attached randomly, always to the root
or always to the neighboring word. However, there are limits to what it can do;
for example it cannot always recognize whether a comma is introduced to separate
the block to its left or to its right. Hence if the punctuation before running
this block is almost good, the block may actually do more harm than good.

Since the punctuation should not have children, we should not create a non-projectivity
if we check the roof edges going to the right.
However, it is still possible that we will attach the punctuation non-projectively
by joining a non-projectivity that already exists.
For example, the left neighbor (node i-1) may have its parent at i-3,
and the node i-2 forms a gap (does not depend on i-3).
"""
from udapi.core.block import Block


class FixPunct(Block):
    """Make sure punct nodes are attached punctuation is attached projectively."""

    def process_node(self, node):
        # TODO fix punct-child
        if node.upos != "PUNCT" or not node.is_leaf():
            return

        # Initialize the candidates (left and right) with the nearest nodes excluding punctuation.
        l_cand, r_cand = node.prev_node, node.next_node
        while l_cand.ord > 0 and l_cand.upos == "PUNCT":
            l_cand = l_cand.prev_node
        while r_cand is not None and r_cand.upos == "PUNCT":
            r_cand = r_cand.next_node

        # Climb up from the candidates, until we would reach the root or "cross" the punctuation.
        if l_cand.is_root():
            l_cand = None
        else:
            while not l_cand.parent.is_root() and l_cand.parent.precedes(node):
                l_cand = l_cand.parent
        if r_cand is not None:
            while not r_cand.parent.is_root() and node.precedes(r_cand.parent):
                r_cand = r_cand.parent

        # Now select between l_cand and r_cand -- which will be the new parent?
        # The lower one. Note that one if neither is descendant of the other and neither is None
        # (which can happen in rare non-projective cases), we arbitrarily prefer r_cand.
        if l_cand is not None and not l_cand.is_root() and l_cand.is_descendant_of(r_cand):
            node.parent = l_cand
        elif r_cand is not None:
            node.parent = r_cand
