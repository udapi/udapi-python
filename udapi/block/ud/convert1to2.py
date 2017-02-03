"""Block Convert1to2 for converting UD v1 to UD v2.

See http://universaldependencies.org/v2/summary.html for the description of all UD v2 changes.
IMPORTANT: this code does only SOME of the changes and the output should be checked.

Author: Martin Popel, based on
https://github.com/UniversalDependencies/tools/tree/master/v2-conversion
by Sebastian Schuster.
"""
import collections
import logging

from udapi.core.block import Block
from udapi.core.node import find_minimal_common_treelet

DEPREL_CHANGE = {
    "mwe": "fixed",
    "dobj": "obj",
    "nsubjpass": "nsubj:pass",
    "csubjpass": "csubj:pass",
    "auxpass": "aux:pass",
    "name": "flat", # or "flat:name"?
    "foreign": "flat", # or "flat:foreign"?
}

class Convert1to2(Block):
    """Block for converting UD v1 to UD v2."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stats = collections.Counter()

    def process_tree(self, tree):
        """Apply all the changes on the current tree.

        This method is automatically called on each tree by Udapi.
        After doing tree-scope changes (remnants), it calls `process_node` on each node.
        By overriding this method in subclasses
        you can reuse just some of the implemented changes.
        """
        for node in tree.descendants:
            self.change_upos(node)
            self.change_upos_copula(node)
            self.change_deprel_simple(node)
            self.change_neg(node)
            self.change_nmod(node)
            self.change_feat(node)

        # fix_remnants_in_tree() needs access to the whole tree.
        self.fix_remnants_in_tree(tree)

        # reattach_coordinations() must go after fix_remnants_in_tree()
        # E.g. in "Marie went to Paris and Miriam to Prague",
        # we need to first remove the edge remnant(Marie, Miriam) and add conj(went, Miriam),
        # which allows reattach_coordinations() to change cc(went, and) → cc(Miriam,and).
        for node in tree.descendants:
            self.reattach_coordinations(node)

        # Fix the plain-text sentence stored in the '# text =' comment.
        self.fix_text(tree)

    def log(self, node, short_msg, long_msg):
        """Log node.address() + long_msg and add ToDo=short_msg to node.misc."""
        logging.warning('node %s %s: %s', node.address(), short_msg, long_msg)
        if node.is_root():
            pass
        elif node.misc['ToDo']:
            if short_msg not in node.misc['ToDo']:
                node.misc['ToDo'] += ',' + short_msg
        else:
            node.misc['ToDo'] = short_msg
        self.stats[short_msg] += 1

    @staticmethod
    def change_upos(node):
        """CONJ→CCONJ."""
        if node.upos == "CONJ":
            node.upos = "CCONJ"

    @staticmethod
    def change_upos_copula(node):
        """deprel=cop needs upos=AUX (or PRON)."""
        if node.deprel == 'cop' and node.upos not in ("AUX", "PRON"):
            node.upos = "AUX"

    @staticmethod
    def change_deprel_simple(node):
        """mwe→fixed, dobj→obj, *pass→*:pass, name→flat, foreign→flat+Foreign=Yes."""
        if node.deprel == 'foreign':
            node.feats['Foreign'] = 'Yes'
        try:
            node.deprel = DEPREL_CHANGE[node.deprel]
        except KeyError:
            pass

    def change_neg(self, node):
        """neg→advmod/det/ToDo + Polarity=Neg.

        In addition, if there is a node with deprel=neg and upos=INTJ,
        it is checked whether it is possibly a real interjection or a negation particle,
        which should have upos=PART (as documented in
        http://universaldependencies.org/u/pos/PART.html)
        This kind of error (INTJ instead of PART for "не") is common e.g. in Bulgarian v1.4,
        but I hope the rule is language independent (enough to be included here).
        """
        # TODO: Is this specific for English?
        if node.deprel == 'neg':
            if 'Neg' not in node.feats['PronType']:
                node.feats['Polarity'] = 'Neg'

            if node.upos in ['ADV', 'PART']:
                node.deprel = 'advmod'
            elif node.upos == 'DET':
                node.deprel = 'det'
            elif node.upos == 'INTJ':
                node.deprel = 'advmod'
                if self.is_verbal(node.parent):
                    node.upos = 'PART'
            else:
                self.log(node, 'neg', 'deprel=neg upos=%s' % node.upos)

    @staticmethod
    def is_verbal(node):
        """Returns True for verbs and nodes with copula child.

        Used in `change_neg`."""
        return node.upos == 'VERB' or any([child.deprel == 'cop' for child in node.children])

    @staticmethod
    def is_nominal(node):
        """Returns 'no' (for predicates), 'yes' (sure nominals) or 'maybe'.

        Used in `change_nmod`."""
        if node.upos in ["VERB", "AUX", "ADJ", "ADV"]:
            return 'no'
        # Include NUM for examples such as "one of the guys"
        # and DET for examples such as "some/all of them"
        if node.upos in ["NOUN", "PRON", "PROPN", "NUM", "DET"]:
            # check whether the node is a predicate
            # (either has a nsubj/csubj dependendent or a copula dependent)
            if any(["subj" in child.deprel or child.deprel == 'cop' for child in node.children]):
                return 'maybe'
            return 'yes'
        return 'maybe'

    def change_nmod(self, node):
        """nmod→obl if parent is not nominal, but predicate."""
        if node.deprel == 'nmod':
            parent_is_nominal = self.is_nominal(node.parent)
            if parent_is_nominal == 'no':
                node.deprel = 'obl'
            elif parent_is_nominal == 'maybe':
                self.log(node, 'nmod', 'deprel=nmod, but parent is ambiguous nominal/predicate')

    def change_feat(self, node):
        """Negative→Polarity, Aspect=Pro→Prosp, VerbForm=Trans→Conv, Definite=Red→Cons,...

        Also Foreign=Foreign→Yes and
        log if Tense=NarTense=Nar or NumType=GenNumType=Gen is used.
        """
        if node.feats['Negative']:
            node.feats['Polarity'] = node.feats['Negative']
            del node.feats['Negative']
        if node.feats['Aspect'] == 'Pro':
            node.feats['Aspect'] = 'Prosp'
        if node.feats['VerbForm'] == 'Trans':
            node.feats['VerbForm'] = 'Conv'
        if node.feats['Definite'] == 'Red':
            node.feats['Definite'] = 'Cons'
        if node.feats['Foreign'] == 'Foreign':
            node.feats['Foreign'] = 'Yes'
        if node.feats['Tense'] == 'Nar':
            self.log(node, 'nar', 'Tense=Nar not allowed in UD v2')
        if node.feats['NumType'] == 'Gen':
            self.log(node, 'gen', 'NumType=Gen not allowed in UD v2')

    def reattach_coordinations(self, node):
        """cc and punct in coordinations should depend on the immediately following conjunct."""
        if node.deprel == 'cc' or (node.deprel == 'punct' and node.lemma in [',', ';']):
            siblings = node.parent.children
            conjuncts = [n for n in siblings if n.deprel == 'conj']

            # Skip cases when punct is used outside of coordination
            # and when cc is used without any conj sibling, e.g. "And then we left."
            # Both of these cases are allowed by the UDv2 specification.
            # However, there are many annotation/conversion errors
            # where cc follows its parent, which has no conj children (but should have some).
            if not conjuncts:
                if node.deprel == 'cc' and node.parent.precedes(node):
                    self.log(node, 'cc-without-conj', 'cc after its parent with no conjuncts')
                return

            next_conjunct = next((n for n in conjuncts if node.precedes(n)), None)
            if next_conjunct:
                if node.deprel == 'punct':
                    next_sibl = next(n for n in siblings if node.precedes(n) and n.deprel != 'cc')
                    if next_sibl != next_conjunct:
                        self.log(node, 'punct-in-coord', 'punct may be part of coordination')
                        return
                node.parent = next_conjunct
            elif node.deprel == 'cc':
                self.log(node, 'cc-after-conj', 'cc with no following conjunct')

    # ELLIPSIS and remnant→orphan handling:
    # http://universaldependencies.org/u/overview/specific-syntax.html#ellipsis
    # says that if the elided element is a predicate and its children core arguments,
    # one of these core arguments should be promoted as a head
    # and all the other core arguments should depend on it via deprel=orphan.
    # However, there are no hints about how to select the promoted head.
    # https://github.com/UniversalDependencies/docs/issues/396#issuecomment-272414482
    # suggests the following priorities based on deprel (and ignoring word order):
    HEAD_PROMOTION = {'nsubj': 9, 'obj': 8, 'iobj': 7, 'obl': 6, 'advmod': 5, 'csubj': 4,
                      'xcomp': 3, 'ccomp': 2, 'advcl': 1}

    def fix_remnants_in_tree(self, root):
        """Change ellipsis with remnant deprels to UDv2 ellipsis with orphans.

        Remnant's parent is always the correlate (same-role) node.
        Usually, correlate's parent is the head of the whole ellipsis subtree,
        i.e. the first conjunct. However, sometimes remnants are deeper, e.g.
        'Over 300 Iraqis are reported dead and 500 wounded.' with edges:
         nsubjpass(reported, Iraqis)
         nummod(Iraqis, 300)
         remnant(300, 500)
        Let's expect all remnants in one tree are part of the same ellipsis structure.
        TODO: theoretically, there may be more ellipsis structures with remnants in one tree,
              but I have no idea how to distinguish them from the deeper-remnants cases.
        """
        remnants = [n for n in root.descendants if n.deprel == 'remnant']
        if not remnants:
            return

        (first_conjunct, _) = find_minimal_common_treelet(remnants[0].parent.parent, *remnants)
        if first_conjunct == root:
            self.log(remnants[0], 'remnant', "remnants' (+their grandpas') common governor is root")
            return

        # top_remnants = remnants with non-remnant parent,
        # other (so-called "chained") remnants will be solved recursively.
        top_remnants = [n for n in remnants if n.parent.deprel != 'remnant']
        top_remnants.sort(key=lambda n: self.HEAD_PROMOTION.get(n.parent.deprel, 0))
        deprels = [n.parent.deprel for n in top_remnants]
        self._recursive_fix_remnants(top_remnants, deprels, first_conjunct)

    def _recursive_fix_remnants(self, remnants, deprels, first_conjunct):
        chained_remnants = []
        chained_deprels = []
        for remnant, deprel in zip(remnants, deprels):
            # orig_deprel may be useful for debugging and building enhanced dependencies
            remnant.misc['orig_deprel'] = deprel
            child_remnants = [n for n in remnant.children if n.deprel == 'remnant']
            if len(child_remnants) > 1:
                self.log(remnant, 'more-remnant-children', 'more than one remnant child')
            chained_remnants.extend(child_remnants)
            chained_deprels.extend([deprel] * len(child_remnants))

        promoted = remnants.pop()
        promoted.parent = first_conjunct
        promoted.deprel = 'conj'
        # Conjuncts are expected to have the same deprel.
        # If this is the case, the orig_deprel annotation is redundant.
        if first_conjunct.deprel == promoted.misc['orig_deprel']:
            del promoted.misc['orig_deprel']
        for remnant in remnants:
            remnant.parent = promoted
            remnant.deprel = 'orphan'

        if chained_remnants:
            self._recursive_fix_remnants(chained_remnants, chained_deprels, first_conjunct)

    def fix_text(self, root):
        """Make sure `root.text` is filled and matching the forms+SpaceAfter=No."""
        stored = root.text
        computed = root.compute_text()
        if stored is None:
            root.text = computed
        elif stored != computed:
            normalized = ' '.join(stored.split())
            if normalized != computed:
                root.text = normalized
                root.add_comment('ToDoOrigText = ' + stored)
                self.log(root, 'text', 'Sentence string does not agree with the stored text.')

    def process_end(self):
        """Print overall statistics of ToDo counts."""
        logging.warning('ud.Convert1to2 ToDo Overview:')
        total = 0
        for todo, count in sorted(self.stats.items(), key=lambda pair: pair[1]):
            total += count
            logging.warning('%20s %10d', todo, count)
        logging.warning('%20s %10d', 'TOTAL', total)
