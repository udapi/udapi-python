"""Block eval.Conll17 for evaluating LAS,UAS,etc - gold and pred may have different tokenization.

This is a reimplementation of the CoNLL2017 shared task official evaluation script,
http://universaldependencies.org/conll17/evaluation.html

The gold trees and predicted (system-output) trees need to be sentence-aligned
e.g. using `util.ResegmentGold`.
"""
import argparse
import difflib
from collections import Counter
from udapi.core.basewriter import BaseWriter

CLAS_IGNORE = {'aux', 'case', 'cc', 'clf', 'cop', 'det', 'mark', 'punct'}

class Conll17(BaseWriter):
    """Evaluate labeled and unlabeled attachment score (LAS and UAS)."""

    def __init__(self, gold_zone='gold', print_raw=False, print_results=True, **kwargs):
        """Args:
        gold_zone - Which zone contains the gold-standard trees (the other zone contains "pred")?
        print_raw - Print raw counts (pred, gold, Words, LAS) for each sentence.
            This is useful for bootstrap resampling post-processing to get confidence intervals.
        print_results - Print a table with overall results after all document are processed.
        """
        super().__init__(**kwargs)
        self.gold_zone = gold_zone
        self.total_count = Counter()
        self.print_raw = print_raw
        self.print_results = print_results

    def process_tree(self, tree):
        gold_tree = tree.bundle.get_tree(self.gold_zone)
        if tree == gold_tree:
            return
        pred_nodes = tree.descendants
        gold_nodes = gold_tree.descendants
        pred_forms = [n.form.lower() for n in pred_nodes]
        gold_forms = [n.form.lower() for n in gold_nodes]
        matcher = difflib.SequenceMatcher(None, pred_forms, gold_forms, autojunk=False)
        aligned = []
        for diff in matcher.get_opcodes():
            edit, pred_lo, pred_hi, gold_lo, gold_hi = diff
            if edit == 'equal':
                aligned.extend(zip(pred_nodes[pred_lo:pred_hi], gold_nodes[gold_lo:gold_hi]))
        align_map = {tree: gold_tree}
        for p_node, g_node in aligned:
            align_map[p_node] = g_node

        count = Counter()
        count['pred'] = len(pred_nodes)
        count['gold'] = len(gold_nodes)
        count['Words'] = len(aligned)
        count['pred_clas'] = len([n for n in pred_nodes if n.udeprel not in CLAS_IGNORE])
        count['gold_clas'] = len([n for n in gold_nodes if n.udeprel not in CLAS_IGNORE])
        count['alig_clas'] = len([n for _, n in aligned if n.udeprel not in CLAS_IGNORE])

        for p_node, g_node in aligned:
            for attr in ('UPOS', 'XPOS', 'Feats', 'Lemma'):
                if p_node.get_attrs([attr.lower()]) == g_node.get_attrs([attr.lower()]):
                    count[attr] += 1
            if align_map.get(p_node.parent) == g_node.parent:
                count['UAS'] += 1
                if p_node.udeprel == g_node.udeprel:
                    count['LAS'] += 1
                    if g_node.udeprel not in CLAS_IGNORE:
                        count['CLAS'] += 1
        self.total_count.update(count)

        if self.print_raw:
            scores = [str(count[s]) for s in ('pred', 'gold', 'Words', 'LAS')]
            print(' '.join(scores))

    def process_end(self):
        if not self.print_results:
            return

        # Redirect the default filehandle to the file specified by self.files
        self.before_process_document(None)

        metrics = ('Words', 'UPOS', 'XPOS', 'Feats', 'Lemma', 'UAS', 'LAS', 'CLAS')
        print("Metric     | Precision |    Recall |  F1 Score | AligndAcc")
        print("-----------+-----------+-----------+-----------+-----------")
        pred, gold = self.total_count['pred'], self.total_count['gold']
        alig = self.total_count['Words']
        for metric in metrics:
            if metric == 'CLAS':
                pred, gold = self.total_count['pred_clas'], self.total_count['gold_clas']
                alig = self.total_count['alig_clas']
            correct = self.total_count[metric]
            precision = correct / pred if pred else 0
            recall = correct / gold if gold else 0
            alignacc = correct / alig if alig else 0
            fscore = 2 * correct / (pred + gold) if pred + gold else 0
            print("{:11}|{:10.2f} |{:10.2f} |{:10.2f} |{:10.2f}".format(
                metric, 100 * precision, 100 * recall, 100 * fscore, 100 * alignacc))

def main():
    parser = argparse.ArgumentParser()
    # TODO post-process bootstrap
    args = parser.parse_args()

if __name__ == "__main__":
    main()
