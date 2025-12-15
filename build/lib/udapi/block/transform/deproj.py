"""Block Deproj for deprojectivization of pseudo-projective trees à la Nivre & Nilsson (2005).

See ud.transform.Proj for details.
TODO: implement also path and head+path strategies.
"""
from udapi.core.block import Block


class Deproj(Block):
    """De-projectivize the trees à la Nivre & Nilsson (2005)."""

    def __init__(self, strategy='head', label='misc', **kwargs):
        """Create the Deproj block object."""
        super().__init__(**kwargs)
        self.strategy = strategy
        self.label = label

    def process_node(self, node):
        if self.label == 'misc':
            label = node.misc['pproj']
        elif self.label == 'deprel':
            parts = node.sdeprel.split('+', 1)
            if len(parts) == 2:
                label = parts[1]
                node.deprel = node.udeprel + (':' + parts[0] if parts[0] else '')
            else:
                label = ''
        else:
            raise(ValueError('Unknown parameter label=%s' % self.label))
        if label == '':
            return
        reconstructed_parent = self.head_strategy(node, label)
        if reconstructed_parent:
            node.parent = reconstructed_parent

    def head_strategy(self, node, label):
        queue = [n for n in node.parent.children if n != node]  # TODO deque
        while queue:
            adept = queue.pop(0)
            if adept.udeprel == label:
                return adept
            queue.extend(adept.children)
        return None
