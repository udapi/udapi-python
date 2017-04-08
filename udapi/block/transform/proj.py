"""Block Proj for (pseudo-)projectivization of trees à la Nivre & Nilsson (2005).

See http://www.aclweb.org/anthology/P/P05/P05-1013.pdf.
This block tries to replicate Malt parser's projectivization:
http://www.maltparser.org/userguide.html#singlemalt_proj
http://www.maltparser.org/optiondesc.html#pproj-marking_strategy

TODO: implement also path and head+path strategies.

TODO: Sometimes it would be better (intuitively)
to lower the gap-node (if its whole subtree is in the gap
and if this does not cause more non-projectivities)
rather than to lift several nodes whose parent-edge crosses this gap.
We would need another label value (usually the lowering is of depth 1),
but the advantage is that reconstruction of lowered edges
during deprojectivization is simple and needs no heuristics.
"""
from udapi.core.block import Block


class Proj(Block):
    """Projectivize the trees à la Nivre & Nilsson (2005)."""

    def __init__(self, strategy='head', lifting_order='deepest', label='misc', **kwargs):
        """Create the Proj block object."""
        super().__init__(**kwargs)
        self.lifting_order = lifting_order
        self.strategy = strategy
        self.label = label

    def process_tree(self, tree):
        nonprojs = [self.nonproj_info(n) for n in tree.descendants if n.is_nonprojective()]
        for nonproj in sorted(nonprojs, key=lambda info: info[0]):
            self.lift(nonproj[1])

    def nonproj_info(self, node):
        if self.lifting_order == 'shortest':
            return (abs(node.ord - node.parent.ord), node)
        orig_parent = node.parent
        node.parent = node.parent.parent
        depth = 1
        while node.is_nonprojective():
            node.parent = node.parent.parent
            depth += 1
        node.parent = orig_parent
        return (-depth, node)

    def lift(self, node):
        orig_parent = node.parent
        depth = 0
        while node.is_nonprojective():
            node.parent = node.parent.parent
            depth += 1
        if depth == 0:
            return
        self.mark(node, orig_parent.udeprel)

    def mark(self, node, label):
        if self.label == 'misc':
            node.misc['pproj'] = label
        elif self.label == 'deprel':
            node.deprel = '%s:%s+%s' % (node.udeprel, node.sdeprel, label)
        else:
            raise ValueError('Unknown parameter label=%s' % self.label)
