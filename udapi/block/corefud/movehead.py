import logging
from collections import Counter
from udapi.core.block import Block
from udapi.core.node import find_minimal_common_treelet

class MoveHead(Block):
    """Block corefud.MoveHead moves the head to the highest node in each mention."""

    def __init__(self, bugs='warn', **kwargs):
        self.counter = Counter()
        self.bugs = bugs
        super().__init__(**kwargs)

    def find_head(self, mention):
        empty_nodes, non_empty = [], []
        for w in mention.words:
            (empty_nodes if w.is_empty() else non_empty).append(w)
        if empty_nodes:
            self.counter['with_empty'] += 1
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

        (highest, added_nodes) = find_minimal_common_treelet(*non_empty)
        if highest in mention.words:
            return highest, 'treelet'

        if 'warn' in self.bugs:
            logging.warning(f"Non-treelet mention in {mention.head} (nearest common antecedent={highest})")
        if 'mark' in self.bugs:
            mention.head.misc['Bug'] = 'non-treelet-mention'
        for word in mention.words:
            if not word.is_empty() and word.parent not in non_empty:
                return word, 'nontreelet'

        if 'warn' in self.bugs:
            logging.warning(f"Strange mention {mention.head} (nearest common antecedent={highest})")
        if 'mark' in self.bugs:
            mention.head.misc['Bug'] = 'strange-mention'
        return mention.head, 'bug'

    def process_document(self, doc):
        for cluster in doc.coref_clusters.values():
            for mention in cluster.mentions:
                self.counter['total'] += 1
                if len(mention.words) < 2:
                    self.counter['single-word'] += 1
                else:
                    new_head, category = self.find_head(mention)
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
