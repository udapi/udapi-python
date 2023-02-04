from udapi.core.block import Block

class GuessSpan(Block):
    """Block corefud.GuessSpan heuristically fills mention spans, while keeping mention.head"""

    def process_coref_mention(self, mention):
        mwords = mention.head.descendants(add_self=True)
        # TODO add heuristics from corefud.PrintMentions almost_forest=1

        # Add empty nodes that are causing gaps.
        # A node "within the span" whose enhanced parent is in the mentions
        # must be added to the mention as well.
        # "within the span" includes also empty nodes "on the boundary".
        # However, don't add empty nodes which are in a gap cause by non-empty nodes.
        to_add = []
        min_ord = int(mwords[0].ord) if mwords[0].is_empty() else mwords[0].ord - 1
        max_ord = int(mwords[-1].ord) + 1
        root = mention.head.root
        for empty in root.empty_nodes:
            if empty in mwords:
                continue
            if empty.ord > max_ord:
                break
            if empty.ord > min_ord:
                if any(enh['parent'] in mwords for enh in empty.deps):
                    to_add.append(empty)
                elif empty.ord > min_ord + 1 and empty.ord < max_ord - 1:
                    prev_nonempty = root.descendants[int(empty.ord) - 1]
                    next_nonempty = root.descendants[int(empty.ord)]
                    if prev_nonempty in mwords and next_nonempty in mwords:
                        to_add.append(empty)
                    #else: empty.misc['Mark'] = f'not_in_treelet_of_{mention.entity.eid}'
        mention.words = sorted(mwords + to_add)
