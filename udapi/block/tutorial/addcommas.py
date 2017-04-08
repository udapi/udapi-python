"""tutorial.AddCommas block template."""
from udapi.core.block import Block


class AddCommas(Block):
    """Heuristically insert nodes for missing commas."""

    def process_node(self, node):
        if self.should_add_comma_before(node):
            comma = node.create_child(form=',', deprel='punct', upos='PUNCT')
            comma.shift_before_node(node)

    def should_add_comma_before(self, node):
        # TODO: Your task: implement some heuristics
        prev_node = node.prev_node
        if prev_node is None:
            return False
        if prev_node.lemma == 'however':
            return True
        if any(n.deprel == 'appos' for n in prev_node.children):
            return True

        return False
