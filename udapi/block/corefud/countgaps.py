from udapi.core.block import Block
from collections import Counter

class CountGaps(Block):
    """Block corefud.checkConsistency searches for sentence sequences with no coref annotation."""

    def __init__(self, report_per_newdoc=False, report_per_file=True, report_total=True, **kwargs):
        super().__init__(**kwargs)
        self.report_per_newdoc = report_per_newdoc
        self.report_per_file = report_per_file
        self.report_total = report_total
        self._total_counter = Counter()

    def _report_stats(self, counter=None, header_id=None):
        if not counter:
            counter = self._total_counter
        if header_id:
            print(f"============ {header_id} ============")
        for key in sorted(counter):
            print(f"{key:2d}: {counter[key]}")

    def _count_empty_seqs(self, empty_seqs):
        counter = Counter()
        for seq in empty_seqs:
            counter[len(seq)] += 1
        return counter

    def process_document(self, doc):
        file_counter = Counter()
        empty_seqs = []
        curr_seq = []
        newdoc = None
        for i, tree in enumerate(doc.trees):
            if tree.newdoc:
                if i:
                    if curr_seq:
                        empty_seqs.append(curr_seq)
                    newdoc_counter = self._count_empty_seqs(empty_seqs)
                    file_counter.update(newdoc_counter)
                    if self.report_per_newdoc:
                        self._report_stats(newdoc_counter, header_id=newdoc)
                newdoc = tree.newdoc
                empty_seqs = []
                curr_seq = []

            has_mention = any(node.coref_mentions for node in tree.descendants)
            if not has_mention:
                curr_seq.append(tree.sent_id)
            elif curr_seq:
                empty_seqs.append(curr_seq)
                curr_seq = []
        
        if curr_seq:
            empty_seqs.append(curr_seq)
        newdoc_counter = self._count_empty_seqs(empty_seqs)
        file_counter.update(newdoc_counter)
        if self.report_per_newdoc:
            self._report_stats(newdoc_counter, header_id=newdoc)

        if self.report_per_file:
            self._report_stats(file_counter, header_id="FULL DOC")

        self._total_counter.update(file_counter)

    def process_end(self):
        if self.report_total:
            self._report_stats(header_id="TOTAL")
