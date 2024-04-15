"""Delete coreference annotation (Entity|Bridge|SplitAnte) and optionally also empty nodes."""

from udapi.core.block import Block
import udapi.core.coref
import logging

class Delete(Block):

    def __init__(self, coref=True, empty=False, misc=False, **kwargs):
        """Args:
        coref: delete coreference attributes in MISC, i.e (Entity|Bridge|SplitAnte)
        empty: delete all empty nodes and references to them (from DEPS and MISC[Functor])
        misc: delete all attributes in MISC except for SpaceAfter
        """
        super().__init__(**kwargs)
        self.coref = coref
        self.empty = empty
        self.misc = misc

    def is_root_reachable_by_deps(self, node, parents_to_ignore=None):
        """ Check if the root node is reachable from node, possibly after deleting the parents_to_ignore nodes.
        """
        stack = [(node, [])]
        while stack:
            proc_node, path = stack.pop()
            # root is reachable
            if proc_node == node.root:
                break
            # path forms a cycle, the root cannot be reached through this branch
            if proc_node in path:
                continue
            for dep in proc_node.deps:
                # the root cannot be reached through ignored nodes
                if dep['parent'] in parents_to_ignore:
                    continue
                # process the parent recursively
                stack.append((dep['parent'], path + [proc_node]))
        else:
            return False
        return True

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
        if self.coref:
            doc._eid_to_entity = None
        for root in doc.trees:
            if self.empty:
                for node in root.descendants:
                    # process only the nodes dependent on empty nodes
                    if not '.' in node.raw_deps:
                        continue
                    # just remove empty parents if the root remains reachable
                    if self.is_root_reachable_by_deps(node, root.empty_nodes):
                        node.deps = [dep for dep in node.deps if not dep['parent'] in root.empty_nodes]
                    # otherwise propagate to non-empty ancestors
                    else:
                        newdeps = self._deps_ignore_nodes(node, root.empty_nodes)
                        newdeps_sorted = sorted(set((dep['parent'].ord, dep['deprel']) for dep in newdeps))
                        node.raw_deps = '|'.join(f"{p}:{r}" for p, r in newdeps_sorted)

                    if '.' in node.misc['Functor'].split(':')[0]:
                        del node.misc['Functor']
                root.empty_nodes = []

            if self.coref or self.misc:
                for node in root.descendants + root.empty_nodes:
                    if self.misc:
                        node.misc = 'SpaceAfter=No' if node.no_space_after else None
                    if self.coref:
                        node._mentions = []
                        if not self.misc:
                            for attr in ('Entity', 'Bridge', 'SplitAnte'):
                                del node.misc[attr]
