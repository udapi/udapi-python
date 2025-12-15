import logging
from collections import Counter
from udapi.core.block import Block
from udapi.core.node import find_minimal_common_treelet

class MoveHead(Block):
    """Block corefud.MoveHead moves the head to the highest node in each mention."""

    def __init__(self, bugs='warn', keep_head_if_possible=True, **kwargs):
        self.counter = Counter()
        self.bugs = bugs
        self.keep_head_if_possible = keep_head_if_possible
        super().__init__(**kwargs)

    def _eparents(self, node):
        if node._raw_deps != '_':
            return [d['parent'] for d in node.deps]
        if node.parent:
            return [node.parent]
        return []

    def find_head(self, mention):
        mwords = set(mention.words)

        # First, check the simplest case: no empty words and a treelet in basic dependencies.
        basic_heads = [w for w in mention.words if not w.parent or not w.parent in mwords]
        assert basic_heads
        if len(basic_heads) == 1:
            return basic_heads[0], 'treelet'

        # Second, check also enhanced dependencies (but only within basic_heads for simplicity).
        enh_heads = [w for w in basic_heads if not any(p in mwords for p in self._eparents(w))]
        if not enh_heads:
            enh_heads = [w for w in basic_heads if not all(p in mwords for p in self._eparents(w))]
            if not enh_heads:
                return mention.head, 'cycle'
        if len(enh_heads) == 1:
            return enh_heads[0], 'treelet'

        # Third, find non-empty parents (ancestors in future) of empty nodes.
        empty_nodes, non_empty = [], []
        for w in enh_heads:
            (empty_nodes if w.is_empty() else non_empty).append(w)
        if empty_nodes:
            for empty_node in empty_nodes:
                parents = [d['parent'] for d in empty_node.deps if not d['parent'].is_empty()]
                if parents:
                    if parents[0] not in non_empty:
                        non_empty.append(parents[0])
                else:
                    # TODO we should climb up, but preventing cycles
                    # We could also introduce empty_node.nonempty_ancestor
                    if 'warn' in self.bugs:
                        logging.warning(f"could not find non-empty parent of {empty_node} for mention {mention.head}")
                    if 'mark' in self.bugs:
                        node.misc['Bug'] = 'no-parent-of-empty'
            non_empty.sort()

        # Fourth, check if there is a node within the enh_heads governing all the mention nodes
        # and forming thus a "gappy treelet", where the head is clearly the "highest" node.
        (highest, added_nodes) = find_minimal_common_treelet(*non_empty)
        if highest in enh_heads:
            return highest, 'gappy'
        if highest in mwords:
            if 'warn' in self.bugs:
                logging.warning(f"Strange mention {mention.head} with highest node {highest}")
            if 'mark' in self.bugs:
                highest.misc['Bug'] = 'highest-in-mwords'
                mention.head.misc['Bug'] = 'highest-head'

        # Fifth, try to convervatively preserve the original head, if it is one of the possible heads.
        if self.keep_head_if_possible and mention.head in enh_heads:
            return mention.head, 'nontreelet'

        # Finally, return the word-order-wise first head candidate as the head.
        return enh_heads[0], 'nontreelet'

    def process_coref_mention(self, mention):
        self.counter['total'] += 1
        if len(mention.words) < 2:
            self.counter['single-word'] += 1
        else:
            new_head, category = self.find_head(mention)
            self.counter[category] += 1
            if new_head is mention.head:
                self.counter[category + '-kept'] += 1
            else:
                self.counter[category + '-moved'] += 1
                mention.head = new_head

    def process_end(self):
        logging.info("corefud.MoveHead overview of mentions:")
        total = self.counter['total']
        for key, value in self.counter.most_common():
            logging.info(f"{key:>16} = {value:6} ({100*value/total:5.1f}%)")
