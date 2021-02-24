from udapi.core.block import Block
from collections import Counter

class Stats(Block):
    """Block corefud.Stats prints various coreference-related statistics."""

    def __init__(self, m_len_max=5, c_len_max=5, focus='non-singletons', **kwargs):
        super().__init__(**kwargs)
        self.m_len_max = m_len_max
        self.c_len_max = c_len_max
        self.focus = focus

        self.counter = Counter()
        self.mentions = 0
        self.clusters = 0
        self.total_nodes = 0
        self.longest_mention = 0
        self.longest_cluster = 0
        self.m_words = 0
        self.m_empty = 0

    def process_document(self, doc):
        self.total_nodes += len(list(doc.nodes))
        for cluster in doc.coref_clusters.values():
            len_mentions = len(cluster.mentions)
            self.longest_cluster = max(len_mentions, self.longest_cluster)
            self.counter[f"c_len_{min(len_mentions, self.c_len_max)}"] += 1
            if len_mentions == 1:
                if self.focus.startswith('non-singletons'):
                    continue
            elif self.focus.startswith('singletons'):
                continue

            self.clusters += 1
            for mention in cluster.mentions:
                self.mentions += 1
                all_words = len(mention.words)
                non_empty = len([w for w in mention.words if not w.is_empty()])
                self.m_words += all_words
                self.m_empty += all_words - non_empty
                self.longest_mention = max(non_empty, self.longest_mention)
                self.counter[f"m_len_{min(non_empty, self.m_len_max)}"] += 1

    def process_end(self):
        mentions = 1 if self.mentions == 0 else self.mentions
        clusters = 1 if self.clusters == 0 else self.clusters
        total_nodes = 1 if self.total_nodes == 0 else self.total_nodes

        if 'clusters' in self.focus:
            clusters_per1k = 1000 * self.clusters / total_nodes
            percents = [100 * self.counter[f"c_len_{i}"] / clusters for i in range(1, self.c_len_max + 1)]
            print(f"{self.clusters:7,} & {clusters_per1k:6.0f} & {self.longest_cluster:6} & "
                + " & ".join(f"{p:5.1f}" for p in percents) + r" \\")
        if self.focus != 'clusters':
            mentions_per1k = 1000 * self.mentions / total_nodes
            percents = [100 * self.counter[f"m_len_{i}"] / mentions for i in range(self.m_len_max + 1)]
            print(f"{self.mentions:7,} & {mentions_per1k:6.0f} & {self.longest_mention:6} & "
                + " & ".join(f"{p:5.1f}" for p in percents) + r" \\")
