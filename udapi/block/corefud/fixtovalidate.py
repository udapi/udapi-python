from udapi.core.block import Block

class FixToValidate(Block):
    """This block fixes the CorefUD data so that the final documents are valid conllu files."""

    def _set_root_deprel(self, doc):
        for node in doc.nodes:
            if node.parent == node.root and node.deprel != "root":
                node.deprel = "root"

    def _space_before_pardoc(self, doc):
        last_node = None
        for i, tree in enumerate(doc.trees):
            if i > 0:
                if (tree.newdoc is not None or tree.newpar is not None) and last_node.no_space_after:
                    del last_node.misc["SpaceAfter"]
            last_node = tree.descendants[-1]

    def process_document(self, doc):
        self._set_root_deprel(doc)
        self._space_before_pardoc(doc)
