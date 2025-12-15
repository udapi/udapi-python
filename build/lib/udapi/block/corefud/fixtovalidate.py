from udapi.core.block import Block

class FixToValidate(Block):
    """This block fixes the CorefUD data so that the final documents are valid conllu files."""

    def _set_root_deprel(self, doc):
        for root in doc.trees:
            for node in root.children:
                if node.deprel != "root":
                    node.deprel = "root"

    def _unset_root_deprel(self, doc):
        for node in doc.nodes:
            parent = node.parent
            if node.deprel == "root" and parent is not None and not parent.is_root():
                #print("\t".join(['Non-0-root:', node.address(), node.upos, str(node.feats), node.parent.upos, str(node.parent.feats)]))
                if parent.upos == "PUNCT" and parent.parent is not None:
                    node.parent = parent.parent
                if node.upos == "CCONJ":
                    node.deprel = "cc"
                elif node.upos == "ADJ" and parent.upos == "PROPN":
                    node.deprel = "amod"
                elif node.upos == "NOUN" and parent.upos == "VERB":
                    node.deprel = "obl"
                else:
                    node.deprel = "parataxis"

    def _space_before_pardoc(self, doc):
        last_node = None
        for i, tree in enumerate(doc.trees):
            if i > 0:
                if (tree.newdoc is not None or tree.newpar is not None) and last_node.no_space_after:
                    del last_node.misc["SpaceAfter"]
            last_node = tree.descendants[-1]

    def process_document(self, doc):
        self._set_root_deprel(doc)
        self._unset_root_deprel(doc)
        self._space_before_pardoc(doc)
