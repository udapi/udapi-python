"""tutorial.AddArticles block template."""
# nickname = xy123
# TODO: make up a unique nickname and edit the previous line
# if you want your results to be listed on the NPFL070 web (under that nickname).
# Delete the line if you don't want to listed on the web.
from udapi.core.block import Block

class AddArticles(Block):
    """Heuristically insert English articles."""

    def process_node(self, node):
        if node.upos == "NOUN":
            the = node.create_child(form="the", lemma="the", upos="DET", deprel="det")
            the.shift_before_subtree(node)
