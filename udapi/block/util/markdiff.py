"""util.MarkDiff is a special block for marking differences between parallel trees."""
import collections
import difflib
import pprint
from udapi.core.block import Block


class MarkDiff(Block):
    """Mark differences between parallel trees."""

    def __init__(self, gold_zone, attributes='form,lemma,upos,xpos,deprel,feats,misc',
                 mark=1, add=False, print_stats=0, **kwargs):
        """Create the Mark block object.
        Params:
        gold_zone: Which of the zones should be treated as gold?
            (The changes are interpreted as from a "pred"=predicted zone into the gold zone.)
        attributes: Which node attributes should be considered when searching for diffs?
            The tree topology, i.e. node parent is always considered.
        mark: What value should be used in `node.misc['Mark']` of the differing nodes?
        add: If False, node.misc attributes Mark, ToDo and Bug will be deleted before running this block,
            so that the marked_only option (e.g. via `udapy -TM`) prints only nodes marked by this block.
        print_stats: How many lines of statistics should be printed? -1 means all.
        """
        super().__init__(**kwargs)
        self.gold_zone = gold_zone
        self.attrs = attributes.split(',')
        self.mark = mark
        self.add = add
        self.print_stats = print_stats
        self.stats = collections.Counter()

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
                        self.stats['ONLY-PARENT-CHANGED'] += 1
            else:
                for node in pred_nodes[pred_lo:pred_hi] + gold_nodes[gold_lo:gold_hi]:
                    node.misc['Mark'] = self.mark
                if self.print_stats:
                    if edit == 'replace':
                        # first n nodes are treated as aligned, the rest is treated as ADDED/DELETED
                        n = min(pred_hi - pred_lo, gold_hi - gold_lo)
                        for p_node, g_node in zip(pred_nodes[pred_lo:pred_lo + n], gold_nodes[gold_lo:gold_lo + n]):
                            for attr in self.attrs:
                                p_value, g_value = p_node._get_attr(attr), g_node._get_attr(attr)
                                if p_value != g_value:
                                    self.stats[f'{attr.upper()}: {p_value} -> {g_value}'] += 1
                            if alignment.get(p_node.parent.ord - 1) != g_node.parent.ord - 1:
                                self.stats['PARENT-CHANGED'] += 1
                        pred_lo, gold_lo = pred_lo + n, gold_lo + n
                    for node in gold_nodes[gold_lo:gold_hi]:
                        self.stats['ADD-WORD'] += 1
                        self.stats['ADD-LEMMA: ' + node.lemma] += 1
                    for node in pred_nodes[pred_lo:pred_hi]:
                        self.stats['DELETE-WORD'] += 1
                        self.stats['DELETE-LEMMA: ' + node.lemma] += 1

    def process_end(self):
        if self.print_stats:
            how_many = None if self.print_stats in (-1, '-1') else self.print_stats
            for edit, count in self.stats.most_common(how_many):
                print(f'{count:4} {edit}')
