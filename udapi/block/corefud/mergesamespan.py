from udapi.core.block import Block
import udapi.core.coref
import itertools
import logging

class MergeSameSpan(Block):
    """
    Multiple same-span mentions are considered invalid in CoNLL-U, whether they
    belong to the same entity or not. If they occur, merge them into one.
    Note: We currently do not have mentions across sentence boundaries in the
    CorefUD data, so this block processes one sentence at a time.
    """

    def __init__(self, same_cluster_only=False, **kwargs):
        super().__init__(**kwargs)
        self.same_cluster_only = same_cluster_only

    def process_tree(self, tree):
        mentions = set()
        for node in tree.descendants_and_empty:
            for m in node.coref_mentions:
                mentions.add(m)

        for mA, mB in itertools.combinations(mentions, 2):
            if self.same_cluster_only and mA.cluster != mB.cluster:
                continue
            # Reduce non-determinism in which mention is removed:
            # If the mentions belong to different entities, sort them by entity (cluster) ids.
            if mA.cluster.eid > mB.cluster.eid:
                mA, mB = mB, mA

            sA, sB = set(mA.words), set(mB.words)
            if sA != sB:
                continue

            # If the mentions belong to different clusters, we should merge the
            # clusters first, i.e., pick one cluster as the survivor, move the
            # mentions from the other cluster to this cluster, and remove the
            # other cluster.
            if mA.cluster != mB.cluster:
                logging.warning(f"Merging same-span mentions that belong to different entities: {mA.cluster.eid} vs. {mB.cluster.eid}")
                ###!!! TODO: As of now, changing the cluster of a mention is not supported in the API.
                #for m in mB.cluster.mentions:
                #    m.cluster = mA.cluster
            # Remove mention B. It may have been removed earlier because of
            # another duplicate, that is the purpose of try-except.
            ###!!! TODO: If we remove a singleton, we are destroying the cluster. Then we must also handle possible bridging and split antecedents pointing to that cluster!
            mB.words = []
            try:
                mB.cluster.mentions.remove(mB)
            except ValueError:
                pass
