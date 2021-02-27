from udapi.core.block import Block
from collections import Counter

class PrintCluster(Block):
    """Block corefud.PrintCluster prints all mentions of a given cluster."""

    def __init__(self, cluster_id, **kwargs):
        super().__init__(**kwargs)
        self.cluster_id = cluster_id

    def process_document(self, doc):
        cluster = doc.coref_clusters.get(self.cluster_id)
        if cluster and cluster.mentions:
            print(f"Coref cluster {self.cluster_id} has {len(cluster.mentions)} mentions in document {doc.meta['docname']}:")
            counter = Counter()
            for mention in cluster.mentions:
                counter[' '.join([w.form for w in mention.words])] += 1
            for form, count in counter.most_common():
                print(f"{count:4}: {form}")
