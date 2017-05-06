"""util.MarkDiff is a special block for marking differences between parallel trees."""
import difflib
from udapi.core.block import Block


class MarkDiff(Block):
    """Mark differences between parallel trees."""

    def __init__(self, gold_zone, attributes='form,lemma,upos,xpos,deprel,feats,misc',
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
        if not self.add:
            for node in tree.descendants + gold_tree.descendants:
                del node.misc['Mark']
                del node.misc['ToDo']
                del node.misc['Bug']

        pred_nodes, gold_nodes = tree.descendants, gold_tree.descendants
        # Make sure both pred and gold trees are marked, even if one has just deleted nodes.
        if len(pred_nodes) != len(gold_nodes):
            tree.add_comment('Mark = %s' % self.mark)
            gold_tree.add_comment('Mark = %s' % self.mark)
        pred_tokens = ['_'.join(n.get_attrs(self.attrs)) for n in pred_nodes]
        gold_tokens = ['_'.join(n.get_attrs(self.attrs)) for n in gold_nodes]
        matcher = difflib.SequenceMatcher(None, pred_tokens, gold_tokens, autojunk=False)
        diffs = list(matcher.get_opcodes())

        alignment = {-1: -1}
        for diff in diffs:
            edit, pred_lo, pred_hi, gold_lo, gold_hi = diff
            if edit in {'equal', 'replace'}:
                for i in range(pred_lo, pred_hi):
                    alignment[i] = i - pred_lo + gold_lo

        for diff in diffs:
            edit, pred_lo, pred_hi, gold_lo, gold_hi = diff
            if edit == 'equal':
                for p_node, g_node in zip(pred_nodes[pred_lo:pred_hi], gold_nodes[gold_lo:gold_hi]):
                    if alignment.get(p_node.parent.ord - 1) != g_node.parent.ord - 1:
                        p_node.misc['Mark'] = self.mark
                        g_node.misc['Mark'] = self.mark
            else:
                for node in pred_nodes[pred_lo:pred_hi] + gold_nodes[gold_lo:gold_hi]:
                    node.misc['Mark'] = self.mark
