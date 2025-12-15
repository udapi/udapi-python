import re
import os.path
from udapi.core.block import Block
from collections import Counter, defaultdict

class PrintEntities(Block):
    """Block corefud.PrintEntities prints all mentions of a given entity."""

    def __init__(self, eid_re=None, min_mentions=0, print_ranges=True, mark_head=True,
                 aggregate_mentions=True, **kwargs):
        """Params:
        eid_re: regular expression constraining ID of the entities to be printed
        min_mentions: print only entities with with at least N mentions
        print_ranges: print also addressess of all mentions
                      (compactly, using the longest common prefix of sent_id)
        mark_head: mark the head (e.g. as "red **car**")
        """
        super().__init__(**kwargs)
        self.eid_re = re.compile(str(eid_re)) if eid_re else None
        self.min_mentions = min_mentions
        self.print_ranges = print_ranges
        self.mark_head = mark_head
        self.aggregate_mentions = aggregate_mentions

    def process_document(self, doc):
        if 'docname' in doc.meta:
            print(f"Coref entities in document {doc.meta['docname']}:")
        for entity in doc.coref_entities:
            if self.eid_re and not self.eid_re.match(entity.eid):
                continue
            if len(entity.mentions) < self.min_mentions:
                continue
            print(f" {entity.eid} has {len(entity.mentions)} mentions:")
            if self.aggregate_mentions:
                counter = Counter()
                ranges = defaultdict(list)
                for mention in entity.mentions:
                    forms = ' '.join([f"**{w.form}**" if self.mark_head and w is mention.head else w.form for w in mention.words])
                    counter[forms] += 1
                    if self.print_ranges:
                        ranges[forms].append(mention.head.root.address() + ':' +mention.span)
                for form, count in counter.most_common():
                    print(f"{count:4}: {form}")
                    if self.print_ranges:
                        if count == 1:
                            print('        ' + ranges[form][0])
                        else:
                            prefix = os.path.commonprefix(ranges[form])
                            print(f'        {prefix} ({" ".join(f[len(prefix):] for f in ranges[form])})')
            else:
                for mention in entity.mentions:
                    forms = ' '.join([f"**{w.form}**" if self.mark_head and w is mention.head else w.form for w in mention.words])
                    print('   ' + forms)
                    if self.print_ranges:
                        print(f"     {mention.head.root.address()}:{mention.span}")
