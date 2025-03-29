from udapi.core.block import Block


class FixParentheses(Block):
    """Find mentions that contain opening parenthesis but do not contain the closing one (or the other way around).
    If the missing parenthesis is an immediate neighbour of the mention span, add it to the span."""

    def __init__(self, mark=True, **kwargs):
        super().__init__(**kwargs)
        self.mark = mark

    def process_coref_mention(self, mention):
        words = [word.lemma for word in mention.words]
        pairs = ['()', '[]', '{}']
        for pair in pairs:
            if pair[0] in words:
                if not pair[1] in words and pair[1] in [node.lemma for node in mention.head.root.descendants]:
                    if mention.words[-1].ord == int(mention.words[-1].ord) and mention.words[-1].next_node and \
                            mention.words[-1].next_node.lemma == pair[1]:
                        next_node = mention.words[-1].next_node
                        mention.words.append(next_node)
                        if self.mark:
                            next_node.misc['Mark'] = 1

            elif pair[1] in words and pair[0] in [node.lemma for node in mention.head.root.descendants]:
                if mention.words[0].ord == int(mention.words[0].ord) and mention.words[0].prev_node \
                        and mention.words[0].prev_node.lemma == pair[0]:
                    prev_node = mention.words[0].prev_node
                    mention.words.append(prev_node)
                    if self.mark:
                        prev_node.misc['Mark'] = 1
