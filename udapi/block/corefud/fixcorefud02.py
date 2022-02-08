from udapi.core.block import Block
import udapi.core.coref
import itertools


class FixCorefUD02(Block):
    """Fix errors in CorefUD 0.2 for release of CorefUD 1.0."""

    def process_document(self, doc):
        for cluster in doc.coref_clusters.values():
            #if cluster.cluster_type:
            #    cluster.cluster_type = cluster.cluster_type.lower()
            for mention in cluster.mentions:
                for bridge in mention.bridging:
                    rel = bridge.relation.lower()
                    if rel.endswith('-inv'):
                        rel = 'i' + rel.replace('-inv', '')
                    rel = rel.replace('-', '')
                    rel = rel.replace('indirect_', '')
                    bridge.relation = rel
