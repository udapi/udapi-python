"""Filter is a special block for keeping/deleting subtrees specified by parameters."""
import re  # may be useful in eval, thus pylint: disable=unused-import

from udapi.core.block import Block

# We need eval in this block
# pylint: disable=eval-used


class Filter(Block):
    """Special block for keeping/deleting subtrees specified by parameters.

    Example usage from command line:
    # extract subtrees governed by nouns (noun phrases)
    `udapy -s util.Filter keep_subtree='node.upos == "NOUN"' < in.conllu > filtered.conllu`

    # keep only trees which contain ToDo|Bug nodes
    udapy -s util.Filter keep_tree_if_node='re.match("ToDo|Bug", str(node.misc))' < in > filtered

    # keep only non-projective trees, annotate non-projective edges with Mark=nonproj and show.
    udapy -T util.Filter keep_tree_if_node='node.is_nonprojective()' mark=nonproj < in | less -R

    # delete trees which contain deprel=remnant
    udapy -s util.Filter delete_tree_if_node='node.deprel == "remnant"' < in > filtered

    # delete subtrees headed by a node with deprel=remnant
    udapy -s util.Filter delete_subtree='node.deprel == "remnant"' < in > filtered
    """

    def __init__(self,  # pylint: disable=too-many-arguments
                 delete_tree=None, delete_tree_if_node=None, delete_subtree=None,
                 keep_tree=None, keep_tree_if_node=None, keep_subtree=None,
                 keep_node=None, mark=None, **kwargs):
        """Create the Filter block object.

        Args:
        `delete_tree`: Python expression to be evaluated for the root and if True,
            the whole tree will be deleted.

        `delete_tree_if_node`: Python expression to be evaluated for each node and if True,
            the whole tree will be deleted.

        `delete_subtree`: Python expression to be evaluated for each node and if True,
                    the subtree headed by `node` will be deleted.

        `keep_tree`: Python expression to be evaluated for the root and if False,
            the whole tree will be deleted.

        `keep_tree_if_node`: Python expression to be evaluated for each node and if True,
            the whole tree will be kept. If the tree contains no node evaluated to True,
            the whole tree will be deleted.

        `keep_subtree`: Python expression to be evaluated for each node and if True,
            the subtree headed by `node` will be marked so it is not deleted.
            All non-marked nodes will be deleted.
            If no node in the tree was marked (i.e. only the root without any children remained),
            the whole tree will be deleted.

        `keep_node`: Python expression to be evaluated for each node and if False,
            the node will be deleted and its children rehanged to its parent.
            Multiple nodes can be deleted (or kept) this way.

        `mark`: a string or None. This makes sense only with `keep_tree_if_node`, where the
            matched nodes are marked with `Mark=<mark>` in `node.misc`, so they will be highlighted
            if printed with `write.TextModeTrees`. Default=None.

        Specifying more than one parameter is not recommended,
        but it is allowed and the current behavior is that
        the arguments are evaluated in the specified order.
        """
        super().__init__(**kwargs)
        self.delete_tree = delete_tree
        self.delete_tree_if_node = delete_tree_if_node
        self.delete_subtree = delete_subtree
        self.keep_tree = keep_tree
        self.keep_tree_if_node = keep_tree_if_node
        self.keep_subtree = keep_subtree
        self.keep_node = keep_node
        self.mark = mark

    def process_tree(self, tree):  # pylint: disable=too-many-branches
        root = tree

        if self.delete_tree is not None:
            if eval(self.delete_tree):
                tree.remove()
                return

        if self.delete_tree_if_node is not None:
            for node in tree.descendants:
                if eval(self.delete_tree_if_node):
                    tree.remove()
                    return

        if self.delete_subtree is not None:
            for node in tree.descendants:
                if eval(self.delete_subtree):
                    node.remove()
                    continue

        if self.keep_tree is not None:
            if not eval(self.keep_tree):
                tree.remove()
                return

        if self.keep_tree_if_node is not None:
            found = False
            for node in tree.descendants:
                if eval(self.keep_tree_if_node):
                    found = True
                    if self.mark:
                        node.misc['Mark'] = self.mark
                    else:
                        return
            if not found:
                tree.remove()
            return

        if self.keep_subtree is not None:
            kept_subtrees = []
            for node in tree.descendants:
                if eval(self.keep_subtree):
                    kept_subtrees.append(node)
            if not kept_subtrees:
                tree.remove()
                return
            else:
                for node in kept_subtrees:
                    node.parent = root
                for orig_subroot in [n for n in root.children if n not in kept_subtrees]:
                    orig_subroot.remove()

        if self.keep_node is not None:
            nodes_to_delete = [node for node in tree.descendants if not eval(self.keep_node)]
            if nodes_to_delete == tree.descendants:
                tree.remove()
                return
            for node in nodes_to_delete:
                node.remove(children='rehang')
