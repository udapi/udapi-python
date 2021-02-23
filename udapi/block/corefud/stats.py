from udapi.core.block import Block
from collections import Counter
import pprint

class Stats(Block):
    """Block corefud.Stats prints various coreference-related statistics."""

    def __init__(self, m_len_max=5, **kwargs):
        super().__init__(**kwargs)
        self.m_len_max = m_len_max

        self.counter = Counter()
        self.mentions = 0
        self.clusters = 0
        self.nodes = 0
        self.longest_mention = 0

    def process_document(self, doc):
        self.nodes += len(list(doc.nodes))
        for cluster in doc.coref_clusters.values():
            self.clusters += 1
            for mention in cluster.mentions:
                self.mentions += 1
                words = len(mention.words)
                self.longest_mention = max(words, self.longest_mention)
                self.counter[f"m_len_{min(words, self.m_len_max)}"] += 1

    def process_end(self):
        #pprint.pprint(self.counter)
        mentions_per1k = 1000 * self.mentions / self.nodes
        percents = [100 * self.counter[f"m_len_{i}"]/self.mentions for i in range(self.m_len_max + 1)]
        print(f"{self.mentions:6} & {mentions_per1k:6.0f} & {self.longest_mention:6} & "
              + " & ".join(f"{p:3.0f}" for p in percents) + r" \\")
