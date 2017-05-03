"""util.MarkDiff is a special block for marking differences between parallel trees."""
from udapi.core.block import Block

class MarkDiff(Block):
    """Mark differences between parallel trees."""

    def __init__(self, gold_zone, attributes='form,p_ord,lemma,upos,xpos,deprel,feats,misc',
                 mark=1, add=False, **kwargs):
        """Create the Mark block object."""
        super().__init__(**kwargs)
        self.gold_zone = gold_zone
        self.attrs = attributes.split(',')
        self.mark = mark
        self.add = add

    def process_tree(self, tree):
        gold_tree = tree.bundle.get_tree(self.gold_zone)
        if tree == gold_tree:
            return
        nodes, gold_nodes = tree.descendants, gold_tree.descendants
        if len(nodes) != len(gold_nodes):
            # TODO use eval.F1.find_lcs
            tree.misc['Mark'] = self.mark
        else:
            for node, gold_node in zip(nodes, gold_nodes):
                self.diff_nodes(node, gold_node)

    def diff_nodes(self, node, gold_node):
        """Compare attributes of two nodes and mark if different."""
        label = '_'.join(node.get_attrs(self.attrs))
        gold_label = '_'.join(gold_node.get_attrs(self.attrs))
        if not self.add:
            del node.misc['Mark']
            del node.misc['ToDo']
            del node.misc['Bug']
            del gold_node.misc['Mark']
            del gold_node.misc['ToDo']
            del gold_node.misc['Bug']
        if label != gold_label:
            node.misc['Mark'] = self.mark
            gold_node.misc['Mark'] = self.mark
