from udapi.core.block import Block
from collections import defaultdict, Counter

class CountGaps(Block):
    """Block corefud.checkConsistency searches for sentence sequences with no coref annotation."""

    def __init__(self, report_per_newdoc=False, report_per_file=True, report_total=True, **kwargs):
        super().__init__(**kwargs)
        self.report_per_newdoc = report_per_newdoc
        self.report_per_file = report_per_file
        self.report_total = report_total
        self._total_counter = defaultdict(Counter)

    def _report_stats(self, counter, header_id=None):
        if header_id:
            print(f"============ {header_id} ============")
        for key in sorted(counter):
            print(f"{key:2d}: {counter[key]}")
        print("-------")
        print(f"SUM: {sum([k*counter[k] for k in counter])}")

    def _count_empty_seqs(self, empty_seqs):
        counter = Counter()
        for seq in empty_seqs:
            counter[len(seq)] += 1
        return counter

    def process_document(self, doc):
        file_counters = defaultdict(Counter)
        empty_seqs = []
        empty_pars = []
        curr_seq = []
        curr_par = []
        is_empty_par = True
        newdoc = None
        for i, tree in enumerate(doc.trees):
            if tree.newdoc:
                if i:
                    if curr_seq:
                        empty_seqs.append(curr_seq)
                    newdoc_seq_counter = self._count_empty_seqs(empty_seqs)
                    file_counters["seq"].update(newdoc_seq_counter)
                    if is_empty_par:
                        empty_pars.append(curr_par)
                    newdoc_par_counter = self._count_empty_seqs(empty_pars)
                    file_counters["par"].update(newdoc_par_counter)
                    if self.report_per_newdoc:
                        self._report_stats(newdoc_seq_counter, header_id=f"SEQ STATS in {newdoc}")
                        self._report_stats(newdoc_par_counter, header_id=f"PAR STATS in {newdoc}")
                newdoc = tree.newdoc
                empty_seqs = []
                empty_pars = []
                curr_seq = []
                curr_par = []
                is_empty_par = True
            if tree.newpar:
                if not tree.newdoc and is_empty_par:
                    empty_pars.append(curr_par)
                curr_par = []
                is_empty_par = True

            has_mention = any(node.coref_mentions for node in tree.descendants)
            if not has_mention:
                curr_seq.append(tree.sent_id)
                curr_par.append(tree.sent_id)
            else:
                if curr_seq:
                    empty_seqs.append(curr_seq)
                    curr_seq = []
                is_empty_par = False
        
        if curr_seq:
            empty_seqs.append(curr_seq)
        newdoc_seq_counter = self._count_empty_seqs(empty_seqs)
        file_counters["seq"].update(newdoc_seq_counter)
        if curr_par:
            empty_pars.append(curr_par)
        newdoc_par_counter = self._count_empty_seqs(empty_pars)
        file_counters["par"].update(newdoc_par_counter)
        if self.report_per_newdoc:
            self._report_stats(newdoc_seq_counter, header_id=f"SEQ STATS, {newdoc}")
            self._report_stats(newdoc_par_counter, header_id=f"PAR STATS, {newdoc}")

        if self.report_per_file:
            self._report_stats(file_counters["seq"], header_id="SEQ STATS, FILE")
            self._report_stats(file_counters["par"], header_id="PAR STATS, FILE")

        self._total_counter["seq"].update(file_counters["seq"])
        self._total_counter["par"].update(file_counters["par"])

    def process_end(self):
        if self.report_total:
            self._report_stats(self._total_counter["seq"], header_id="SEQ STATS, TOTAL")
            self._report_stats(self._total_counter["par"], header_id="PAR STATS, TOTAL")
