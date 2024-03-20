"""Delete coreference annotation (Entity|Bridge|SplitAnte) and optionally also empty nodes."""

from udapi.core.block import Block
import udapi.core.coref
import logging

class Delete(Block):

    def __init__(self, empty=False, **kwargs):
        super().__init__(**kwargs)
        self.empty = empty

    def process_document(self, doc):
        # This block should work both with coreference loaded (deserialized) and not.
        doc._eid_to_entity = None
        for root in doc.trees:
            if self.empty:
                root.empty_nodes = []
                for node in root.descendants:
                    if node.raw_deps != '_':
                        node.raw_deps = '|'.join(d for d in node.raw_deps.split('|') if not '.' in d)
                        if node.raw_deps == '':
                            node.raw_deps = '0:root'
                    if '.' in node.misc['Functor'].split(':')[0]:
                        del node.misc['Functor']

            for node in root.descendants + root.empty_nodes:
                node._mentions = []
                for attr in ('Entity', 'Bridge', 'SplitAnte'):
                    del node.misc[attr]
