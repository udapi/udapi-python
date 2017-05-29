"""util.ResegmentGold is a block for sentence alignment and re-segmentation of two zones."""
from udapi.core.block import Block
from udapi.core.mwt import MWT
from udapi.core.root import Root


class ResegmentGold(Block):
    """Sentence-align two zones (gold and pred) and resegment the pred zone.

    The two zones must contain the same sequence of characters.
    """

    def __init__(self, gold_zone, **kwargs):
        """Args:
        gold_zone: which zone contains the gold segmentation
        """
        super().__init__(**kwargs)
        self.gold_zone = gold_zone

    def process_document(self, document):
        pred_trees = []
        for bundle in reversed(document.bundles):
            zones = [t.zone for t in bundle.trees]
            if len(zones) > 2 or (len(zones) == 2 and self.gold_zone not in zones):
                raise ValueError('Expected two zones, but found: ' + str(zones))
            for tree in bundle.trees:
                if tree.zone != self.gold_zone:
                    pred_trees.append(tree)
                    tree.remove()
        for bundle in document.bundles:
            if not bundle.trees:
                bundle.remove()
        if not document.bundles:
            raise ValueError('No bundles with gold_zone=' + self.gold_zone)

        for bundle in document.bundles:
            g_tree = bundle.trees[0]
            p_tree = pred_trees.pop()
            g_chars = ''.join(t.form for t in g_tree.token_descendants).replace(' ', '')
            p_chars = ''.join(t.form for t in p_tree.token_descendants).replace(' ', '')
            if g_chars == p_chars:
                bundle.add_tree(p_tree)
                continue
            while len(g_chars) > len(p_chars):
                if not pred_trees:
                    _print(document)
                    print(g_chars)
                    print(p_chars)
                    raise ValueError('no pred_trees')
                new_p_tree = pred_trees.pop()
                p_chars += ''.join(t.form for t in new_p_tree.token_descendants).replace(' ', '')
                p_tree.steal_nodes(new_p_tree.descendants)
            if not p_chars.startswith(g_chars):
                g_tree.print_subtree()
                print('---------------------- p_chars do not start with g_chars')
                p_tree.print_subtree()
                raise ValueError('p_chars do not start with g_chars')
                # index = 0
                # while g_chars[index] == p_chars[index]:
                #     index += 1
                # raise ValueError(
                #     "The concatenation of tokens in the gold and pred trees differ!\n" +
                #     "First 20 differing characters in gold: '%s' and pred: '%s'"
                #     % (g_chars[index:index + 20], p_chars[index:index + 20]))
            if g_chars == p_chars:
                bundle.add_tree(p_tree)
                continue

            # p_tree contains more nodes than it should
            p_chars = ''
            tokens = p_tree.token_descendants
            old_words = []
            for index, token in enumerate(tokens):
                p_chars += token.form.replace(' ', '')
                if len(p_chars) > len(g_chars):
                    # TODO
                    g_tree.print_subtree()
                    print('----------------------')
                    p_tree.print_subtree()
                    raise ValueError('Cannot solve token over sentence boundary')
                if len(p_chars) == len(g_chars):
                    next_p_tree = Root(sent_id=p_tree.bundle.bundle_id + '-split2/' + p_tree.zone)
                    words = [t.words if isinstance(t, MWT) else t for t in tokens[index + 1:]]
                    next_p_tree.steal_nodes(words)
                    pred_trees.append(next_p_tree)
                    bundle.add_tree(p_tree)
                    break
                else:
                    if isinstance(token, MWT):
                        old_words.extend(token.words)
                    else:
                        old_words.append(token)


def _print(doc):
    for bun in doc.bundles:
        for tre in bun.trees:
            tre.print_subtree()
