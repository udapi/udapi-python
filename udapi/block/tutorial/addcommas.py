"""tutorial.AddCommas block template."""
from udapi.core.block import Block

# nickname = xy123
# TODO: make up a unique nickname and edit the previous line
# if you want your results to be listed on the NPFL070 web (under that nickname).
# Delete the line if you don't want to listed on the web.

class AddCommas(Block):
    """Heuristically insert nodes for missing commas."""

    def __init__(self, language='en', **kwargs):
        """Create the AddCommas block object.

        Args:
        `language`: which language-specific rules to use ('en' or 'cs')
        """
        super().__init__(**kwargs)
        self.language = language

    def process_node(self, node):
        if self.should_add_comma_before(node):
            comma = node.create_child(form=',', deprel='punct', upos='PUNCT')
            comma.shift_before_node(node)

    def should_add_comma_before(self, node):
        # TODO: Your task: implement some heuristics
        prev_node = node.prev_node
        if prev_node is None:
            return False
        if self.language == 'en' and node.lemma == 'however':
            return True
        if any(n.deprel == 'appos' for n in prev_node.children):
            return True

        return False
