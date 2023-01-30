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

    def __init__(self, feats=True, misc=True, **kwargs):
        """
        Args:
        `feats`: normalize the ordering of FEATS. Default=True.
        `misc`: normalize the ordering of MISC. Default=True.
        """
        super().__init__(**kwargs)
        self.feats = feats
        self.misc = misc
        # TODO: normalize also standardized comments like text, sent_id,...

    def process_node(self, node):
        if self.feats:
            node.feats._deserialize_if_empty()
            node.feats._string = None
        if self.misc:
            node.misc._deserialize_if_empty()
            node.misc._string = None
