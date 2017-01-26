"""Filter is a special block for keeping/deleting subtrees specified by parameters."""
from udapi.core.block import Block

# We need eval in this block
# pylint: disable=eval-used
class Filter(Block):
    """Special block for keeping/deleting some subtrees specified by parameters.

    Example usage from command line:
    # extract subtrees governed by nouns (noun phrases)
    `udapy -s util.Filter subtree='node.upos == "NOUN"' < in.conllu > filtered.conllu`

    TODO:
    Currently, only the first matching node (and its subtree) is kept,
    all other nodes are deleted (although some of them may be matching as well).
    In future, there should be a parameter `keep_all` for changing this behavior.

    Also, there should be parameters `node`, `tree` (maybe more) for specifying
    other conditions. It should be possible to keep the whole tree which contains
    a matching node.
    """

    def __init__(self, subtree, delete_matching=False, **kwargs):
        """Create the Filter block object.

        Args:
        `subtree`: Python expression to be evaluated and if True,
            the subtree headed by `node` is considered "matching"
        `delete_matching` (default=False): by default the matching subtrees are kept
            and all other nodes are deleted. Specifying `delete_matching=True` inverts
            this behavior, so only the matching nodes and their subtrees are deleted.
        """
        super().__init__(**kwargs)
        self.subtree = subtree
        self.delete_matching = delete_matching

    def process_tree(self, tree):
        root = tree
        found = False
        for node in tree.descendants:
            if eval(self.subtree):
                found = True
                if self.delete_matching:
                    node.remove()
                else:
                    node.parent = root
                    for sibling in [n for n in root.children if n != node]:
                        sibling.remove()
                    break
        if not found and not self.delete_matching:
            tree.remove()
