from udapi.core.block import Block
from collections import Counter

class Stats(Block):
    """Block corefud.Stats prints various coreference-related statistics."""

    def __init__(self, m_len_max=5, c_len_max=5, report_mentions=True, report_clusters=True,
                 exclude_singletons=False, exclude_nonsingletons=False, style='human', **kwargs):
        super().__init__(**kwargs)
        self.m_len_max = m_len_max
        self.c_len_max = c_len_max
        self.report_mentions = report_mentions
        self.report_clusters = report_clusters
        self.exclude_singletons = exclude_singletons
        self.exclude_nonsingletons = exclude_nonsingletons
        self.style = style
        if style not in 'tex human'.split():
            raise ValueError(f'Unknown style f{style}')

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
            if len_mentions == 1 and self.exclude_singletons:
                continue
            elif len_mentions > 1 and self.exclude_nonsingletons:
                continue
            self.longest_cluster = max(len_mentions, self.longest_cluster)
            self.counter['c_total_len'] += len_mentions
            self.counter[f"c_len_{min(len_mentions, self.c_len_max)}"] += 1

            self.clusters += 1
            for mention in cluster.mentions:
                self.mentions += 1
                all_words = len(mention.words)
                non_empty = len([w for w in mention.words if not w.is_empty()])
                self.m_words += all_words
                self.m_empty += all_words - non_empty
                self.longest_mention = max(non_empty, self.longest_mention)
                self.counter['m_total_len'] += non_empty
                self.counter[f"m_len_{min(non_empty, self.m_len_max)}"] += 1

    def process_end(self):
        mentions_nonzero = 1 if self.mentions == 0 else self.mentions
        clusters_nonzero = 1 if self.clusters == 0 else self.clusters
        total_nodes_nonzero = 1 if self.total_nodes == 0 else self.total_nodes

        columns =[ ]
        if self.report_clusters:
            columns += [('clusters', f"{self.clusters:7,}"),
                        ('clusters_per1k', f"{1000 * self.clusters / total_nodes_nonzero:6.0f}"),
                        ('longest_cluster', f"{self.longest_cluster:6}"),
                        ('avg_cluster', f"{self.counter['c_total_len'] / self.clusters:5.1f}")]
            for i in range(1, self.c_len_max + 1):
                percent = 100 * self.counter[f"c_len_{i}"] / clusters_nonzero
                columns.append((f"c_len_{i}{'' if i < self.c_len_max else '+'}", f"{percent:5.1f}"))
        if self.report_mentions:
            columns += [('mentions', f"{self.mentions:7,}"),
                        ('mentions_per1k', f"{1000 * self.mentions / total_nodes_nonzero:6.0f}"),
                        ('longest_mention', f"{self.longest_mention:6}"),
                        ('avg_mention', f"{self.counter['m_total_len'] / self.mentions:5.1f}")]
            for i in range(0, self.m_len_max + 1):
                percent = 100 * self.counter[f"m_len_{i}"] / mentions_nonzero
                columns.append((f"m_len_{i}{'' if i < self.m_len_max else '+'}", f"{percent:5.1f}"))

        if self.style == 'tex':
            print(" & ".join(c[1] for c in columns))
        elif self.style == 'human':
            for c in columns:
                print(f"{c[0]:>15} = {c[1].strip():>10}")
