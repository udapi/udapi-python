from udapi.core.block import Block
import udapi.core.coref
import itertools

class MarkCrossing(Block):
    """Find mentions with crossing spans."""

    def __init__(self, same_cluster_only=False, continuous_only=False, print_form=False, **kwargs):
        super().__init__(**kwargs)
        self.same_cluster_only = same_cluster_only
        self.continuous_only = continuous_only
        self.print_form = print_form

    def _print(self, mention):
        if self.print_form:
            return ' '.join([w.form for w in mention.words])
        else:
            return mention.span

    def process_node(self, node):
        if len(node.coref_mentions) > 1:
            for mA, mB in itertools.combinations(node.coref_mentions, 2):
                if not (set(mA.words) <= set(mB.words)) and not (set(mB.words) <= set(mA.words)):
                    if self.same_cluster_only and mA.cluster != mB.cluster:
                        continue
                    if self.continuous_only and (',' in mA.span or ',' in mB.span):
                        continue
                    node.misc['Mark'] = f'cross:{self._print(mA)}+{self._print(mB)}'
