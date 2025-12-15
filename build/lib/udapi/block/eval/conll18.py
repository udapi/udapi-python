r"""Block&script eval.Conll18 for evaluating LAS,UAS,etc as in CoNLL2018 UD shared task.

This is a reimplementation of the CoNLL2018 shared task official evaluation script,
http://universaldependencies.org/conll18/evaluation.html

The gold trees and predicted (system-output) trees need to be sentence-aligned
e.g. using `util.ResegmentGold`.
Unlike in `eval.Parsing`, the gold and predicted trees can have different tokenization.

An example usage and output::

    $ udapy read.Conllu zone=gold files=gold.conllu \
            read.Conllu zone=pred files=pred.conllu ignore_sent_id=1 \
            util.ResegmentGold \
            eval.Conll18
    Metric     | Precision |    Recall |  F1 Score | AligndAcc
    -----------+-----------+-----------+-----------+-----------
    Words      |     27.91 |     52.17 |     36.36 |    100.00
    UPOS       |     27.91 |     52.17 |     36.36 |    100.00
    XPOS       |     27.91 |     52.17 |     36.36 |    100.00
    Feats      |     27.91 |     52.17 |     36.36 |    100.00
    Lemma      |     27.91 |     52.17 |     36.36 |    100.00
    UAS        |     16.28 |     30.43 |     21.21 |     58.33
    LAS        |     16.28 |     30.43 |     21.21 |     58.33
    CLAS       |     10.34 |     16.67 |     12.77 |     37.50


For evaluating multiple systems and testsets (as in CoNLL2018)
stored in `systems/system_name/testset_name.conllu` you can use::

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
                  eval.Conll18 print_results=0 print_raw=LAS \
                  > results/$sys/${testset%.conllu}
        done
    done
    python3 `python3 -c 'import udapi.block.eval.conll18 as x; print(x.__file__)'` -r 100

The last line executes this block as a script and computes bootstrap resampling with 100 resamples
(default=1000, it is recommended to keep the default or higher value unless testing the interface).
This prints the ranking and confidence intervals (95% by default) and also p-values for each
pair of systems with neighboring ranks. If the difference in LAS is significant
(according to a paired bootstrap test, by default if p < 0.05),
a line is printed between the two systems.

The output looks like::

     1.          Stanford 76.17 ± 0.12 (76.06 .. 76.30) p=0.001
    ------------------------------------------------------------
     2.              C2L2 74.88 ± 0.12 (74.77 .. 75.01) p=0.001
    ------------------------------------------------------------
     3.               IMS 74.29 ± 0.13 (74.16 .. 74.43) p=0.001
    ------------------------------------------------------------
     4.          HIT-SCIR 71.99 ± 0.14 (71.84 .. 72.12) p=0.001
    ------------------------------------------------------------
     5.           LATTICE 70.81 ± 0.13 (70.67 .. 70.94) p=0.001
    ------------------------------------------------------------
     6.        NAIST-SATO 70.02 ± 0.13 (69.89 .. 70.16) p=0.001
    ------------------------------------------------------------
     7.    Koc-University 69.66 ± 0.13 (69.52 .. 69.79) p=0.002
    ------------------------------------------------------------
     8.   UFAL-UDPipe-1-2 69.36 ± 0.13 (69.22 .. 69.49) p=0.001
    ------------------------------------------------------------
     9.            UParse 68.75 ± 0.14 (68.62 .. 68.89) p=0.003
    ------------------------------------------------------------
    10.     Orange-Deskin 68.50 ± 0.13 (68.37 .. 68.62) p=0.448
    11.          TurkuNLP 68.48 ± 0.14 (68.34 .. 68.62) p=0.029
    ------------------------------------------------------------
    12.              darc 68.29 ± 0.13 (68.16 .. 68.42) p=0.334
    13.  conll18-baseline 68.25 ± 0.14 (68.11 .. 68.38) p=0.003
    ------------------------------------------------------------
    14.             MQuni 67.93 ± 0.13 (67.80 .. 68.06) p=0.062
    15.             fbaml 67.78 ± 0.13 (67.65 .. 67.91) p=0.283
    16.     LyS-FASTPARSE 67.73 ± 0.13 (67.59 .. 67.85) p=0.121
    17.        LIMSI-LIPN 67.61 ± 0.14 (67.47 .. 67.75) p=0.445
    18.             RACAI 67.60 ± 0.13 (67.46 .. 67.72) p=0.166
    19.     IIT-Kharagpur 67.50 ± 0.14 (67.36 .. 67.64) p=0.447
    20.           naistCL 67.49 ± 0.15 (67.34 .. 67.63)
"""
import argparse
import difflib
import logging
import os
import random
import sys
from collections import Counter
from udapi.core.basewriter import BaseWriter

CONTENT = {'nsubj', 'obj', 'iobj', 'csubj', 'ccomp', 'xcomp', 'obl', 'vocative', 'expl',
           'dislocated', 'advcl', 'advmod', 'discourse', 'nmod', 'appos', 'nummod', 'acl',
           'amod', 'conj', 'fixed', 'flat', 'compound', 'list', 'parataxis', 'orphan', 'goeswith',
           'reparandum', 'root', 'dep'}
FUNCTIONAL = {'aux', 'cop', 'mark', 'det', 'clf', 'case', 'cc'}
UNIV_FEATS = {'PronType', 'NumType', 'Poss', 'Reflex', 'Foreign', 'Abbr', 'Gender', 'Animacy',
              'Number', 'Case', 'Definite', 'Degree', 'VerbForm', 'Mood', 'Tense', 'Aspect',
              'Voice', 'Evident', 'Polarity', 'Person', 'Polite'}

class Conll18(BaseWriter):
    """Evaluate LAS, UAS, MLAS and BLEX."""

    def __init__(self, gold_zone='gold', print_raw=False, print_results=True, print_counts=False,
                 **kwargs):
        """Args:
        gold_zone - Which zone contains the gold-standard trees (the other zone contains "pred")?
        print_raw - Print raw counts (pred, gold, aligned, correct) for each sentence.
            This is useful for bootstrap resampling post-processing to get confidence intervals.
            The parameter print_raw specifies a given metric
            (UAS, LAS, MLAS, BLEX, UPOS, XPOS, Feats, Lemma) or is 0 (or False) by default.
        print_results - Print a table with overall results after all document are processed.
        print_counts - Print counts of correct/gold/system instead of prec/rec/f1 for all metrics.
        """
        super().__init__(**kwargs)
        self.gold_zone = gold_zone
        self.total_count = Counter()
        self.print_raw = print_raw
        self.print_results = print_results
        self.print_counts = print_counts

    def _ufeats(self, feats):
        return '|'.join(sorted(x for x in feats.split('|') if x.split('=', 1)[0] in UNIV_FEATS))

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
        align_map, feats_match = {tree: gold_tree}, {}
        for p_node, g_node in aligned:
            align_map[p_node] = g_node
            feats_match[p_node] = self._ufeats(str(p_node.feats)) == self._ufeats(str(g_node.feats))

        count = Counter()
        count['pred'] = len(pred_nodes)
        count['gold'] = len(gold_nodes)
        count['Words'] = len(aligned)
        count['pred_cont'] = len([n for n in pred_nodes if n.udeprel in CONTENT])
        count['gold_cont'] = len([n for n in gold_nodes if n.udeprel in CONTENT])
        count['alig_cont'] = len([n for _, n in aligned if n.udeprel in CONTENT])

        for p_node, g_node in aligned:
            count['UPOS'] += 1 if p_node.upos == g_node.upos else 0
            count['XPOS'] += 1 if p_node.xpos == g_node.xpos else 0
            count['Lemmas'] += 1 if g_node.lemma == '_' or p_node.lemma == g_node.lemma else 0
            count['UFeats'] += 1 if feats_match[p_node] else 0
            if feats_match[p_node] and p_node.upos == g_node.upos and p_node.xpos == g_node.xpos:
                count['AllTags'] += 1
            if align_map.get(p_node.parent) == g_node.parent and not p_node.misc['Rehanged']:
                count['UAS'] += 1
                if p_node.udeprel == g_node.udeprel:
                    count['LAS'] += 1
                    if g_node.udeprel in CONTENT:
                        count['CLAS'] += 1
                        if g_node.lemma == '_' or g_node.lemma == p_node.lemma:
                            count['BLEX'] += 1
                        if self._morpho_match(p_node, g_node, align_map, feats_match):
                            if not p_node.misc['FuncChildMissing']:
                                count['MLAS'] += 1
        self.total_count.update(count)

        if self.print_raw:
            if self.print_raw in {'CLAS', 'BLEX', 'MLAS'}:
                scores = [str(count[s]) for s in ('pred_cont', 'gold_cont', 'alig_cont',
                                                  self.print_raw)]
            else:
                scores = [str(count[s]) for s in ('pred', 'gold', 'Words', self.print_raw)]
            print(' '.join(scores))

    def _morpho_match(self, p_node, g_node, align_map, feats_match):
        if p_node.upos != g_node.upos or not feats_match[p_node]:
            return False
        p_children = [c for c in p_node.children if c.udeprel in FUNCTIONAL and not c.misc['Rehanged']]
        g_children = [c for c in g_node.children if c.udeprel in FUNCTIONAL]
        if len(p_children) != len(g_children):
            return False
        for p_child, g_child in zip(p_children, g_children):
            if align_map.get(p_child) != g_child:
                return False
            if p_child.udeprel != g_child.udeprel:
                return False
            if p_child.upos != g_child.upos or not feats_match[p_child]:
                return False
        return True

    def process_end(self):
        if not self.print_results:
            return

        # Redirect the default filehandle to the file specified by self.files
        self.before_process_document(None)

        metrics = ('Words', 'UPOS', 'XPOS', 'UFeats', 'AllTags',
                   'Lemmas', 'UAS', 'LAS', 'CLAS', 'MLAS', 'BLEX')
        if self.print_counts:
            print("Metric     | Correct   |      Gold | Predicted | Aligned")
        else:
            print("Metric     | Precision |    Recall |  F1 Score | AligndAcc")
        print("-----------+-----------+-----------+-----------+-----------")
        for metric in metrics:
            correct = self.total_count[metric]
            if metric in {'CLAS', 'BLEX', 'MLAS'}:
                pred, gold = self.total_count['pred_cont'], self.total_count['gold_cont']
                alig = self.total_count['alig_cont']
            else:
                pred, gold = self.total_count['pred'], self.total_count['gold']
                alig = self.total_count['Words']
            if self.print_counts:
                print("{:11}|{:10} |{:10} |{:10} |{:10}".format(
                    metric, correct, gold, pred, alig))
            else:
                precision, recall, fscore, alignacc = prec_rec_f1(correct, pred, gold, alig)
                alignacc = "{:10.2f}".format(100 * alignacc) if metric != 'Words' else ""
                print("{:11}|{:10.2f} |{:10.2f} |{:10.2f} |{}".format(
                    metric, 100 * precision, 100 * recall, 100 * fscore, alignacc))


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
            pred, gold, words, correct = ([0] * len(tests) for _ in range(4))
            for _ in range(samples):
                i_test, pre, gol, wor, corr = random.choice(results[i_system])
                pred[i_test] += pre
                gold[i_test] += gol
                words[i_test] += wor
                correct[i_test] += corr
            fscore_sum = 0
            for i_test in range(len(tests)):
                _prec, _rec, fscore, _aligacc = prec_rec_f1(correct[i_test], pred[i_test], gold[i_test])
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
