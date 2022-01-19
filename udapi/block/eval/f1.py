"""Block eval.F1 for evaluating differences between sentences with P/R/F1.

``eval.F1 zones=en_pred gold_zone=en_gold details=0``
prints something like::

  predicted =     210
  gold      =     213
  correct   =     210
  precision = 100.00%
  recall    =  98.59%
  F1        =  99.29%

``eval.F1 gold_zone=y attributes=form,upos focus='(?i:an?|the)_DET' details=4``
prints something like::

  === Details ===
  token       pred  gold  corr   prec     rec      F1
  the_DET      711   213   188  26.44%  88.26%  40.69%
  The_DET       82    25    19  23.17%  76.00%  35.51%
  a_DET          0    62     0   0.00%   0.00%   0.00%
  an_DET         0    16     0   0.00%   0.00%   0.00%
  === Totals ===
  predicted =     793
  gold      =     319
  correct   =     207
  precision =  26.10%
  recall    =  64.89%
  F1        =  37.23%

This block finds differences between nodes of trees in two zones
and reports the overall precision, recall and F1.
The two zones are "predicted" (on which this block is applied)
and "gold" (which needs to be specified with parameter ``gold``).

This block also reports the number of total nodes in the predicted zone
and in the gold zone and the number of "correct" nodes,
that is predicted nodes which are also in the gold zone.
By default two nodes are considered "the same" if they have the same ``form``,
but it is possible to check also for other nodes' attributes
(with parameter ``attributes``).

As usual::

  precision = correct / predicted
  recall = correct / gold
  F1 = 2 * precision * recall / (precision + recall)

The implementation is based on finding the longest common subsequence (LCS)
between the nodes in the two trees.
This means that the two zones do not need to be explicitly word-aligned.
"""
from collections import Counter
import logging
import re

from udapi.core.basewriter import BaseWriter

# pylint: disable=too-many-instance-attributes,invalid-name


class F1(BaseWriter):
    """Evaluate differences between sentences (in different zones) with P/R/F1.

    Args:
    zones: Which zone contains the "predicted" trees?
           Make sure that you specify just one zone.
           If you leave the default value "all" and the document contains more zones,
           the results will be mixed, which is most likely not what you wanted.
           Exception: If the document conaints just two zones (predicted and gold trees),
           you can keep the default value "all" because this block
           will skip comparison of the gold zone with itself.

    gold_zone: Which zone contains the gold-standard trees?

    attributes: comma separated list of attributes which should be checked
                when deciding whether two nodes are equivalent in LCS

    focus: Regular expresion constraining the tokens we are interested in.
           If more attributes were specified in the ``attributes`` parameter,
           their values are concatenated with underscore, so ``focus`` should reflect that
           e.g. ``attributes=form,upos focus='(a|the)_DET'``.
           For case-insensitive focus use e.g. ``focus='(?i)the'``
           (which is equivalent to ``focus='[Tt][Hh][Ee]'``).

    details: Print also detailed statistics for each token (matching the ``focus``).
             The value of this parameter ``details`` specifies the number of tokens to include.
             The tokens are sorted according to the sum of their *predicted* and *gold* counts.
    """

    def __init__(self, gold_zone, attributes='form', focus=None, details=4, **kwargs):
        """Create the eval.F1 block object."""
        super().__init__(**kwargs)
        self.gold_zone = gold_zone
        self.attrs = attributes.split(',')
        self.focus = None
        if focus is not None:
            self.focus = re.compile(focus)
        self.details = details
        self.correct, self.pred, self.gold = 0, 0, 0
        self.visited_zones = Counter()
        if details:
            self._common = Counter()
            self._pred = Counter()
            self._gold = Counter()
            self._total = Counter()

    def process_tree(self, tree):
        gold_tree = tree.bundle.get_tree(self.gold_zone)
        if tree == gold_tree:
            return
        self.visited_zones[tree.zone] += 1

        pred_tokens = ['_'.join(n.get_attrs(self.attrs, undefs='None')) for n in tree.descendants]
        gold_tokens = ['_'.join(n.get_attrs(self.attrs, undefs='None')) for n in gold_tree.descendants]

        # lcs("abc", "acb") can be either "ab" or "ac".
        # We want to prefer the LCS with the highest number of non-focused tokens.
        # E.g. if focus="," then lcs("a,c", "ac,") should be "ac" and the comma should be evaluated
        # as non-aligned, i.e. eval.F1 should return precision=recall=f1=0 for this sentence.
        if self.focus is None:
            common = find_lcs(pred_tokens, gold_tokens)
        else:
            nf_pred_tokens = [x for x in pred_tokens if not self.focus.fullmatch(x)]
            nf_gold_tokens = [x for x in gold_tokens if not self.focus.fullmatch(x)]
            nf_common = find_lcs(nf_pred_tokens, nf_gold_tokens)
            i, j, c, un_pred, un_gold, common  = 0, 0, 0, [], [], []
            while i < len(pred_tokens) and j < len(gold_tokens):
                if c == len(nf_common):
                    common += find_lcs(pred_tokens[i+1:], gold_tokens[j+1:])
                    break
                while nf_common[c] != pred_tokens[i]:
                    un_pred.append(pred_tokens[i])
                    i += 1
                while nf_common[c] != gold_tokens[j]:
                    un_gold.append(gold_tokens[j])
                    j += 1
                common += find_lcs(un_pred, un_gold)
                un_pred, un_gold  = [], []
                while c < len(nf_common) and nf_common[c] == pred_tokens[i] and nf_common[c] == gold_tokens[j]:
                    i, j, c = i+1, j+1, c+1
            common = [x for x in common if self.focus.fullmatch(x)]
            pred_tokens = [x for x in pred_tokens if self.focus.fullmatch(x)]
            gold_tokens = [x for x in gold_tokens if self.focus.fullmatch(x)]

        self.correct += len(common)
        self.pred += len(pred_tokens)
        self.gold += len(gold_tokens)

        if self.details:
            for x in common:
                self._common[x] += 1
            for x in gold_tokens:
                self._gold[x] += 1
                self._total[x] += 1
            for x in pred_tokens:
                self._pred[x] += 1
                self._total[x] += 1

    def process_end(self):
        # Redirect the default filehandle to the file specified by self.files
        self.before_process_document(None)

        if not self.visited_zones:
            logging.warning('Block eval.F1 was not applied to any zone. '
                            'Check the parameter zones=%s', self.zones)
        elif len(self.visited_zones) > 1:
            logging.warning('Block eval.F1 was applied to more than one zone %s. '
                            'The results are mixed together. Check the parameter zones=%s',
                            list(self.visited_zones.elements()), self.zones)
        print('Comparing predicted trees (zone=%s) with gold trees (zone=%s), sentences=%d'
              % (next(self.visited_zones.elements()), self.gold_zone,
                 self.visited_zones.most_common(1)[0][1]))
        if self.details:
            print('=== Details ===')
            print('%-10s %5s %5s %5s %6s  %6s  %6s'
                  % ('token', 'pred', 'gold', 'corr', 'prec', 'rec', 'F1'))
            tokens = self._total.most_common(self.details)
            for token, _ in tokens:
                _prec = self._common[token] / (self._pred[token] or 1)
                _rec = self._common[token] / (self._gold[token] or 1)
                _f1 = 2 * _prec * _rec / ((_prec + _rec) or 1)
                print('%-10s %5d %5d %5d %6.2f%% %6.2f%% %6.2f%%'
                      % (token, self._pred[token], self._gold[token], self._common[token],
                         100 * _prec, 100 * _rec, 100 * _f1))
            print('=== Totals ===')

        print("%-9s = %7d\n" * 3
              % ('predicted', self.pred, 'gold', self.gold, 'correct', self.correct), end='')
        pred, gold = self.pred or 1, self.gold or 1  # prevent division by zero
        precision = self.correct / pred
        recall = self.correct / gold
        f1 = 2 * precision * recall / ((precision + recall) or 1)
        print("%-9s = %6.2f%%\n" * 3
              % ('precision', 100 * precision, 'recall', 100 * recall, 'F1', 100 * f1), end='')


# difflib.SequenceMatcher does not compute LCS, so let's implement it here
def find_lcs(x, y):
    """Find longest common subsequence."""
    m, n = len(x), len(y)
    if m == 0 or n == 0:
        return []
    elif x[0] == y[0]:
        i = 1
        while i < min(m, n) and x[i] == y[i]:
            i += 1
        return x[:i] + (find_lcs(x[i:], y[i:]) if i < min(m, n) else [])
    else:
        C = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                C[i][j] = C[i - 1][j - 1] + 1 if x[i - 1] == y[j - 1] else max(C[i][j - 1], C[i - 1][j])
        index = C[m][n]
        lcs = [None] * index
        while m > 0 and n > 0:
            if x[m - 1] == y[n - 1]:
                lcs[index - 1] = x[m - 1]
                m, n, index = m - 1, n - 1, index - 1
            elif C[m - 1][n] > C[m][n - 1]:
                m -= 1
            else:
                n -= 1
        return lcs
