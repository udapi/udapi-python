"""Block ud.Basic2Enhanced for copying basic dependencies to enhanced where missing.

UD treebanks are not required to have enhanced dependencies (https://universaldependencies.org/u/overview/enhanced-syntax.html).
However, if such annotation is present (in the DEPS column of CoNLL-U),
it must be present in all nodes and all nodes must be reachable from the root
in the enhanced-deps graph (as checked by the validator).
There may be use cases where enhanced deps are annotated only in some kinds of nodes (e.g. empty nodes)
and the rest of nodes is expected to be the same as in the basic dependencies.
To make such file valid, one can use this block.

This block should not be used on a file with no enhanced dependencies:
It makes no sense to just duplicate the HEAD+DEPREL information also in the DEPS column.
"""
from udapi.core.block import Block


class Basic2Enhanced(Block):
    """Make sure DEPS column is always filled."""

    def process_tree(self, tree):
        for node in tree.descendants_and_empty:
            if node.raw_deps == "_":
                node.raw_deps = f"{node.parent.ord}:{node.deprel}"
