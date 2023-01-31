from udapi.core.block import Block

class GuessSpan(Block):
    """Block corefud.GuessSpan heuristically fills mention spans, while keeping mention.head"""

    def process_coref_mention(self, mention):
        mention.words = mention.head.descendants(add_self=True)
        # TODO add empty nodes that are causing gaps
        # TODO add heuristics from corefud.PrintMentions almost_forest=1
