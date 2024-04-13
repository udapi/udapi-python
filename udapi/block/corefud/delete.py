"""Delete coreference annotation (Entity|Bridge|SplitAnte) and optionally also empty nodes."""

from udapi.core.block import Block
import udapi.core.coref
import logging

class Delete(Block):

    def __init__(self, empty=False, **kwargs):
        super().__init__(**kwargs)
        self.empty = empty


    def _deps_ignore_nodes(self, node, parents_to_ignore):
        """ Retrieve deps from the node, recursively ignoring specified parents.
        """
        newdeps = []
        stack = [(node, [])]
        while stack:
            proc_node, skipped_nodes = stack.pop()
            # if there is a cycle of skipped nodes, ground the subtree to the root
            if proc_node in skipped_nodes:
                newdeps.append({'parent': node.root, 'deprel': 'root'})
                continue
            for dep in proc_node.deps:
                # keep deps with a parent that shouldn't be ignored
                if not dep['parent'] in parents_to_ignore:
                    newdeps.append(dep)
                    continue
                # process the ignored parent recursively
                stack.append((dep['parent'], skipped_nodes + [proc_node]))
        return newdeps

    def process_document(self, doc):
        # This block should work both with coreference loaded (deserialized) and not.
        doc._eid_to_entity = None
        for root in doc.trees:
            if self.empty:
                for node in root.descendants:
                    # process only the nodes dependent on empty nodes
                    if not '.' in node.raw_deps:
                        continue
                    newdeps = self._deps_ignore_nodes(node, root.empty_nodes)
                    newdeps_sorted = sorted(set((dep['parent'].ord, dep['deprel']) for dep in newdeps))
                    node.raw_deps = '|'.join(f"{p}:{r}" for p, r in newdeps_sorted)

                    if '.' in node.misc['Functor'].split(':')[0]:
                        del node.misc['Functor']
                root.empty_nodes = []

            for node in root.descendants + root.empty_nodes:
                node._mentions = []
                for attr in ('Entity', 'Bridge', 'SplitAnte'):
                    del node.misc[attr]
