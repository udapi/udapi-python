"""tutorial.AddArticles block template."""
from udapi.core.block import Block

class AddArticles(Block):
    """Heuristically insert English articles."""

    def process_node(self, node):
        if node.upos == "NOUN":
            the = node.create_child(form="the", lemma="the", upos="DET", deprel="det")
            the.shift_before_subtree(node)
