"""util.Normalize normalizes the ordering of various attributes in CoNLL-U."""
from udapi.core.block import Block
from pathlib import Path

class Normalize(Block):
    """Normalize the ordering of attributes in the FEATS and MISC columns.

    The attribute-value pairs in the FEATS column in CoNLL-U files
    must be sorted alphabetically (case-insensitive) according to the guidelines
    (https://universaldependencies.org/format.html#morphological-annotation).
    The same is highly recommended for the MISC column.
    It is useful e.g. for comparing two conllu files with diff.

    Udapi does the sorting automatically, but for speed reasons
    only when writing into these attributes.
    This block thus just forces deserialization of node.feats and node.misc,
    so that the Udapi later sorts the attributes during serialization.
    It is a bit more efficient than something like
    util.Eval node='node.feats["Number"] = node.feats["Number"]'
    or
    util.Eval node='node.misc["NonExistentAttribute"] = None'
    """

    def __init__(self, feats=True, misc=True, sent_id=False, empty_node_ord=False, start_sent_id=1, sent_id_prefix="",
                 sent_id_from_filename=False, sent_id_reset_at_newdoc=False, newdoc_from_filename=False, **kwargs):
        """
        Args:
        `feats`: normalize the ordering of FEATS. Default=True.
        `misc`: normalize the ordering of MISC. Default=True.
        `sent_id`: normalize sent_id so it forms a sequence of integers. Default=False.
        `empty_node_ord`: normalize ord attributes of empty nodes. Default=False.
        `start_sent_id`: the first sent_id number
        `sent_id_prefix`: a string to be prepended before the integer sent_id. Default=empty string.
        `sent_id_from_filename`: add Path(doc.meta["loaded_from"]).stem before the `sent_id_prefix`. Default=False.
        `sent_id_reset_at_newdoc`: reset the sent_id counter to 1 for each new document. Default=False.
        `newdoc_from_filename`: set newdoc to Path(doc.meta["loaded_from"]).stem. Default=False.
        """
        super().__init__(**kwargs)
        self.feats = feats
        self.misc = misc
        self.sent_id = sent_id
        self.empty_node_ord = empty_node_ord
        self.next_sent_id = start_sent_id
        self.sent_id_prefix = sent_id_prefix
        self.sent_id_from_filename = sent_id_from_filename
        self.sent_id_reset_at_newdoc = sent_id_reset_at_newdoc
        self.newdoc_from_filename = newdoc_from_filename
        if sent_id_reset_at_newdoc and not sent_id_from_filename:
            raise ValueError("Cannot use sent_id_reset_at_newdoc without sent_id_from_filename")
        if sent_id_prefix or start_sent_id != 1 or sent_id_from_filename:
            self.sent_id = True

        # TODO: normalize also the order of standardized comments like text, sent_id,...

    def process_bundle(self, bundle):
        is_newdoc = any(tree.newdoc for tree in bundle.trees)
        if self.newdoc_from_filename and is_newdoc:
            tree = next(tree for tree in bundle.trees if tree.newdoc)
            tree.newdoc = Path(bundle.document.meta["loaded_from"]).stem
        if self.sent_id:
            if self.sent_id_reset_at_newdoc and is_newdoc:
                self.next_sent_id = 1
            prefix = self.sent_id_prefix
            if self.sent_id_from_filename:
                prefix = Path(bundle.document.meta["loaded_from"]).stem + prefix
            bundle.bundle_id = prefix + str(self.next_sent_id)
            self.next_sent_id += 1

        for tree in bundle:
            if self._should_process_tree(tree):
                self.process_tree(tree)

    def process_tree(self, tree):
        if self.empty_node_ord:
            node_ord, empty_ord = 0, 0
            for node in tree.descendants_and_empty:
                if node.is_empty():
                    empty_ord += 1
                    old_empty_ord, new_empty_ord = str(node.ord), f"{node_ord}.{empty_ord}"
                    if old_empty_ord != new_empty_ord:
                        # Make sure all nodes in this sentence have deserialized enhanced deps.
                        for n in tree.descendants_and_empty:
                            n.deps
                        node.ord = new_empty_ord
                else:
                    empty_ord = 0
                    node_ord = node.ord
        for node in tree.descendants:
            self.process_node(node)

    def process_node(self, node):
        if self.feats:
            node.feats._deserialize_if_empty()
            node.feats._string = None
        if self.misc:
            node.misc._deserialize_if_empty()
            node.misc._string = None
