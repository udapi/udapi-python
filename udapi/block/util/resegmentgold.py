"""util.ResegmentGold is a block for sentence alignment and re-segmentation of two zones."""
from udapi.core.block import Block
from udapi.core.mwt import MWT
from udapi.core.root import Root


class ResegmentGold(Block):
    """Sentence-align two zones (gold and pred) and resegment the pred zone.

    The two zones must contain the same sequence of characters.
    """

    def __init__(self, gold_zone='gold', **kwargs):
        """Args:
        gold_zone: which zone contains the gold segmentation
        """
        super().__init__(**kwargs)
        self.gold_zone = gold_zone

    def process_document(self, document):
        if not document.bundles:
            return
        pred_trees = self.extract_pred_trees(document)

        for bundle_no, bundle in enumerate(document.bundles):
            g_tree = bundle.trees[0]
            p_tree = pred_trees.pop()
            g_chars = ''.join(t.form for t in g_tree.token_descendants).replace(' ', '')
            p_chars = ''.join(t.form for t in p_tree.token_descendants).replace(' ', '')
            if g_chars == p_chars:
                bundle.add_tree(p_tree)
                continue

            # Make sure that p_tree contains enough nodes.
            while len(p_chars) < len(g_chars):
                if not pred_trees:
                    raise ValueError('no pred_trees:\n%s\n%s' % (p_chars, g_chars))
                new_p_tree = pred_trees.pop()
                p_chars += ''.join(t.form for t in new_p_tree.token_descendants).replace(' ', '')
                p_tree.steal_nodes(new_p_tree.descendants)
            self.choose_root(p_tree, g_tree)
            if not p_chars.startswith(g_chars):
                raise ValueError('p_chars do not start with g_chars:\n%s\n%s' % (p_chars, g_chars))
            if g_chars == p_chars:
                bundle.add_tree(p_tree)
                continue

            # Now p_tree contains more nodes than it should.
            p_chars = ''
            tokens = p_tree.token_descendants
            for index, token in enumerate(tokens):
                p_chars += token.form.replace(' ', '')
                if len(p_chars) > len(g_chars):
                    # TODO
                    g_tree.print_subtree()
                    print('----------------------')
                    p_tree.print_subtree()
                    raise ValueError('Cannot solve token over sentence boundary')
                if len(p_chars) == len(g_chars):
                    next_p_tree = Root(zone=p_tree.zone)
                    words = []
                    for token in tokens[index + 1:]:
                        if isinstance(token, MWT):
                            words.extend(token.words)
                        else:
                            words.append(token)
                    next_p_tree.steal_nodes(words)
                    self.choose_root(p_tree, g_tree)
                    self.choose_root(next_p_tree, document.bundles[bundle_no + 1].trees[0])
                    pred_trees.append(next_p_tree)
                    bundle.add_tree(p_tree)
                    break

    def extract_pred_trees(self, document):
        """Delete all trees with zone!=gold_zone from the document and return them."""
        pred_trees = []
        for bundle in reversed(document.bundles):
            zones = [t.zone for t in bundle.trees]
            if len(zones) > 2 or (len(zones) == 2 and self.gold_zone not in zones):
                raise ValueError('Expected two zones including gold_zone=%s, but found: %s'
                                 % (self.gold_zone, zones))
            for tree in bundle.trees:
                if tree.zone != self.gold_zone:
                    pred_trees.append(tree)
                    tree.remove()
        for bundle in document.bundles:
            if not bundle.trees:
                bundle.remove()
        if not document.bundles:
            raise ValueError('No bundles with gold_zone=' + self.gold_zone)
        return pred_trees

    @staticmethod
    def choose_root(p_tree, g_tree):
        """Prevent multiple roots, which are forbidden in the evaluation script."""
        p_subroots = p_tree.children
        if len(p_subroots) > 1:
            g_subroot_form = g_tree.children[0]
            p_subroot = next((n for n in p_subroots if n.form == g_subroot_form), p_subroots[0])
            for false_subroot in (n for n in p_subroots if n != p_subroot):
                false_subroot.parent = p_subroot
                false_subroot.deprel = 'dep:wrong-' + false_subroot.deprel
