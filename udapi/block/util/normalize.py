"""util.Normalize normalizes the ordering of various attributes in CoNLL-U."""
from udapi.core.block import Block

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

    def __init__(self, feats=True, misc=True, sent_id=False, start_sent_id=1, sent_id_prefix="", **kwargs):
        """
        Args:
        `feats`: normalize the ordering of FEATS. Default=True.
        `misc`: normalize the ordering of MISC. Default=True.
        `sent_id`: normalize sent_id so it forms a sequence of integers. Default=False.
        `start_sent_id`: the first sent_id number
        `sent_id_prefix`: a string to be prepended before the integer sent_id. Default=empty string.
        """
        super().__init__(**kwargs)
        self.feats = feats
        self.misc = misc
        self.sent_id = sent_id
        self.next_sent_id = start_sent_id
        self.sent_id_prefix = sent_id_prefix
        if sent_id_prefix or start_sent_id != 1:
            self.sent_id = True
        # TODO: normalize also the order of standardized comments like text, sent_id,...

    def process_bundle(self, bundle):
        if self.sent_id:
            bundle.bundle_id = self.sent_id_prefix + str(self.next_sent_id)
            self.next_sent_id += 1

        for tree in bundle:
            if self._should_process_tree(tree):
                self.process_tree(tree)

    def process_tree(self, tree):
        for node in tree.descendants:
            self.process_node(node)

    def process_node(self, node):
        if self.feats:
            node.feats._deserialize_if_empty()
            node.feats._string = None
        if self.misc:
            node.misc._deserialize_if_empty()
            node.misc._string = None
