from udapi.core.block import Block
import udapi.core.coref
import itertools

class FixInterleaved(Block):
    """Fix mentions with interleaved or crossing spans."""

    def __init__(self, same_cluster_only=True, both_discontinuous=False,
                 crossing_only=False, nested_same_subspan=True, **kwargs):
        super().__init__(**kwargs)
        self.same_cluster_only = same_cluster_only
        self.both_discontinuous = both_discontinuous
        self.crossing_only = crossing_only
        self.nested_same_subspan = nested_same_subspan

    def process_tree(self, tree):
        mentions = set()
        for node in tree.descendants_and_empty:
            for m in node.coref_mentions:
                mentions.add(m)

        for mA, mB in itertools.combinations(mentions, 2):
            if self.same_cluster_only and mA.cluster != mB.cluster:
                continue

            # Fully nested spans are OK, expect for same-subspan
            sA, sB = set(mA.words), set(mB.words)
            if (sA <= sB) or (sB <= sA):
                if not self.nested_same_subspan:
                    continue
                elif not set(mA.span.split(',')).intersection(set(mB.span.split(','))):
                    continue

            # Crossing or interleaved+crossing?
            elif self.crossing_only:
                if not sA.intersection(sB):
                    continue
            else:
                if mA.words[0] < mB.words[0] and mA.words[-1] < mB.words[0]:
                    continue
                if mB.words[0] < mA.words[0] and mB.words[-1] < mA.words[0]:
                    continue

            if self.both_discontinuous and (',' not in mA.span or ',' not in mB.span):
                continue

            mA.words = list(sA.union(sB))
            for wb in sB:
                try:
                    wb._mentions.remove(mB)
                except ValueError:
                    pass
            try:
                mB.cluster.mentions.remove(mB)
            except ValueError:
                pass
