"""Block&script eval.Conll17 for evaluating LAS,UAS,etc as in CoNLL2017 UD shared task.

This is a reimplementation of the CoNLL2017 shared task official evaluation script,
http://universaldependencies.org/conll17/evaluation.html

The gold trees and predicted (system-output) trees need to be sentence-aligned
e.g. using `util.ResegmentGold`.
Unlike in `eval.Parsing`, the gold and predicted trees can have different tokenization.

Example execution::

    #!/bin/bash
    SYSTEMS=`ls systems`
    [[ $# -ne 0 ]] && SYSTEMS=$@
    set -x
    set -e
    for sys in $SYSTEMS; do
        mkdir -p results/$sys
        for testset in `ls systems/$sys`; do
            udapy read.Conllu zone=gold files=gold/$testset \
                  read.Conllu zone=pred files=systems/$sys/$testset ignore_sent_id=1 \
                  util.ResegmentGold \
                  eval.Conll17 print_results=0 print_raw=1 \
                  > results/$sys/${testset%.conllu}
        done
    done
    python3 `python3 -c 'import udapi.block.eval.conll17 as x; print(x.__file__)'` -r 100

The last line executes this block as a script and computes bootstrap resampling with 100 resamples
(default=1000, it is recommended to keep the default or higher value unless testing the interface).
This prints the ranking and confidence intervals (95% by default) and also p-values for each
pair of systems with neighboring ranks. If the difference in LAS is significant
(according to a paired bootstrap test, by default if p < 0.05),
a line is printed between the two systems.

TODO: Bootstrap currently reports only LAS, but all the other measures could be added as well.
"""
import argparse
import difflib
import logging
import os
import random
import sys
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


def prec_rec_f1(correct, pred, gold, alig=0):
    precision = correct / pred if pred else 0
    recall = correct / gold if gold else 0
    alignacc = correct / alig if alig else 0
    fscore = 2 * correct / (pred + gold) if pred + gold else 0
    return precision, recall, fscore, alignacc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir_results", "-d", default="results", help="directory with results")
    parser.add_argument("--resamples", "-r", default=1000, type=int, help="how many resamples")
    parser.add_argument("--confidence", "-c", default=95, help="use x-percent confidence interval")
    parser.add_argument("--tests", "-t", default='all', help="comma-separated test sets")
    parser.add_argument("--systems", "-s", default='all', help="comma-separated systems")
    parser.add_argument("--randseed", default=0, type=int, help="random seed, default=sys time")
    args = parser.parse_args()
    res_dir, resamples, conf = args.dir_results, args.resamples, args.confidence
    alpha = (1 - conf/100) / 2
    index_lo = int(alpha * (resamples - 1))
    index_hi = resamples - 1 - index_lo
    index_mid = int(resamples / 2)
    if args.systems == 'all':
        systems = os.listdir(res_dir)
    else:
        systems = args.systems.split(',')
    if args.tests == 'all':
        tests = set()
        for system in systems:
            tests.update(os.listdir(res_dir + '/' + system))
        tests = sorted(tests)
    else:
        tests = args.tests.split(',')
    if args.randseed:
        random.seed(args.randseed)
    results = []

    print('Loading...', file=sys.stderr)
    for system in systems:
        sys_results = []
        results.append(sys_results)
        for i_test, test in enumerate(tests):
            filename = '/'.join((res_dir, system, test))
            try:
                with open(filename) as res_file:
                    sys_results.extend([[i_test] + list(map(int, l.split())) for l in res_file])
            except FileNotFoundError:
                logging.warning(filename + ' not found')
    samples = len(sys_results)

    print('Resampling...', file=sys.stderr)
    boot_results = []
    for i_resample in range(resamples):
        print(i_resample + 1, file=sys.stderr, end='\r')
        resample_results = []
        boot_results.append(resample_results)
        for i_system in range(len(systems)):
            pred, gold, words, las = ([0] * len(tests) for _ in range(4))
            for _ in range(samples):
                i_test, pre, gol, wor, la_ = random.choice(results[i_system])
                pred[i_test] += pre
                gold[i_test] += gol
                words[i_test] += wor
                las[i_test] += la_
            fscore_sum = 0
            for i_test in range(len(tests)):
                _prec, _rec, fscore, _aligacc = prec_rec_f1(las[i_test], pred[i_test], gold[i_test])
                fscore_sum += fscore
            resample_results.append(fscore_sum / len(tests))
    print('\n', file=sys.stderr)

    sys_fscores = []
    for i_system, system in enumerate(systems):
        sys_fscores.append([boot_results[i_resample][i_system] for i_resample in range(resamples)])
    final_results = []
    sys_sys_wins = [[0] * len(systems) for x in range(len(systems))]
    for i_system, system in enumerate(systems):
        for j_system in range(i_system):
            for i, j in zip(sys_fscores[i_system], sys_fscores[j_system]):
                if i > j:
                    sys_sys_wins[i_system][j_system] += 1
                elif i < j:
                    sys_sys_wins[j_system][i_system] += 1
        fscores = sorted(sys_fscores[i_system])
        final_results.append([i_system, fscores[index_mid], fscores[index_lo], fscores[index_hi]])

    sorted_systems = sorted(final_results, key=lambda x: -x[1])
    for rank, sys_results in enumerate(sorted_systems):
        i_system, f1_mid, f1_lo, f1_hi = sys_results
        if rank < len(systems) - 1:
            j_worse_sys = sorted_systems[rank + 1][0]
            p_value = (sys_sys_wins[j_worse_sys][i_system] + 1) / (resamples + 1)
            p_str = " p=%.3f" % p_value
        else:
            p_value, p_str = 1, ""
        print("%2d. %17s %5.2f ±%5.2f (%5.2f .. %5.2f)%s" %
              (rank + 1, systems[i_system],
               100 * f1_mid, 50 * (f1_hi - f1_lo), 100 * f1_lo, 100 * f1_hi, p_str))
        if p_value < (1 - conf/100):
            print('-' * 60)


if __name__ == "__main__":
    main()
