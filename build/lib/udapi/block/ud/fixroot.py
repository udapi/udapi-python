"""
Block ud.FixRoot will ensure that the tree is free of common root-related errors.
Simple heuristics are used; it is likely that human inspection would lead to
a different solution. Nevertheless, if a quick fix is needed to pass the
validation, this block can be helpful.

WARNING: The block currently ignores enhanced dependencies.
"""
import re
from udapi.core.block import Block


class FixRoot(Block):
    """
    Fixes the following validation errors:
    - Only one node must be attached directly to the artificial root node.
      => If the root has multiple children, keep the first one. Attach the other
         ones to the first one. Change their deprel to 'parataxis'.
    - The node attached as a child of the artificial root node must have the
      'root' relation (or its subtype).
      => If the root child has another deprel, change it to 'root'.
    - The node attached as a child of the artificial root node is the only one
      allowed to have the 'root' relation (or its subtype).
      => If another node has that deprel, change it to 'parataxis'.
    """

    def process_tree(self, root):
        rchildren = root.children
        if len(rchildren) > 1:
            for i in range(len(rchildren)-1):
                rchildren[i+1].parent = rchildren[0]
                rchildren[i+1].deprel = 'parataxis'
        if rchildren[0].udeprel != 'root':
            rchildren[0].deprel = 'root'
        for n in root.descendants:
            if not n.parent == root and n.udeprel == 'root':
                n.deprel = 'parataxis'
