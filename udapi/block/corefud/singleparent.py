"""If an empty node has multiple (enhanced-deps) parents, only the highest one is kept."""
from udapi.core.block import Block
from collections import Counter
from udapi.core.node import find_minimal_common_treelet
import logging

class SingleParent(Block):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._reasons = Counter()

    def process_tree(self, tree):
        for empty in tree.empty_nodes:
            self._reasons['_empty'] += 1
            if len(empty.deps) > 1:
                self._reasons['_more-parents'] += 1
                parents = [d['parent'] for d in empty.deps]
                nonempty_parents = [p for p in parents if not p.is_empty()]
                if len(nonempty_parents) != len(parents):
                    self._reasons['empty-parent'] += 1
                    #empty.misc['Mark'] = f"empty-parent:{empty.deps}"
                    logging.warning(f"Empty node {empty} has an empty parent.")
                if not nonempty_parents:
                    empty.deps = []
                    self._reasons['no-nonempty-parent'] += 1
                    continue
                (highest, added_nodes) = find_minimal_common_treelet(*nonempty_parents)
                if highest in nonempty_parents:
                    self._reasons['one-governs'] += 1
                    empty.deps = [d for d in empty.deps if d['parent'] is highest]
                    continue
                nonempty_parents.sort(key=lambda n:n._get_attr('depth'))
                if len(nonempty_parents)>1 and nonempty_parents[0]._get_attr('depth') == nonempty_parents[0]._get_attr('depth'):
                    self._reasons['same-depth'] += 1
                    #empty.misc['Mark'] = f"same-depth:{empty.deps}"
                else:
                    self._reasons['one-highest'] += 1
                    #empty.misc['Mark'] = f"one-highest:{empty.deps}"
                empty.deps = [d for d in empty.deps if d['parent'] is nonempty_parents[0]]

    def after_process_document(self, document):
        message = "\n"
        for k, v in self._reasons.most_common():
            message += f"{k}={v}\n"
        #document.meta["bugs"] = message
        logging.info(message)
