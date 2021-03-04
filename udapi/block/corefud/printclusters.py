import re
import os.path
from udapi.core.block import Block
from collections import Counter, defaultdict

class PrintClusters(Block):
    """Block corefud.PrintClusters prints all mentions of a given cluster."""

    def __init__(self, id_re=None, min_mentions=0, print_ranges=True, **kwargs):
        """Params:
        id_re: regular expression constraining ClusterId of the clusters to be printed
        min_mentions: print only clusters with with at least N mentions
        print_ranges: print also addressess of all mentions
                      (compactly, using the longest common prefix of sent_id)
        """
        super().__init__(**kwargs)
        self.id_re = re.compile(str(id_re)) if id_re else None
        self.min_mentions = min_mentions
        self.print_ranges = print_ranges

    def process_document(self, doc):
        if 'docname' in doc.meta:
            print(f"Coref clusters in document {doc.meta['docname']}:")
        for cluster in doc.coref_clusters.values():
            if self.id_re and not self.id_re.match(cluster.cluster_id):
                continue
            if len(cluster.mentions) < self.min_mentions:
                continue
            print(f"{cluster.cluster_id} has {len(cluster.mentions)} mentions:")
            counter = Counter()
            ranges = defaultdict(list)
            for mention in cluster.mentions:
                forms = ' '.join([w.form for w in mention.words])
                counter[forms] += 1
                if self.print_ranges:
                    ranges[forms].append(mention.head.root.address() + ':' +mention.span)
            for form, count in counter.most_common():
                print(f"{count:4}: {form}")
                if self.print_ranges:
                    if count == 1:
                        print('      ' + ranges[form][0])
                    else:
                        prefix = os.path.commonprefix(ranges[form])
                        print(f'      {prefix} ({" ".join(f[len(prefix):] for f in ranges[form])})')
