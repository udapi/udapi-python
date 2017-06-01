"""Block Convert1to2 for converting UD v1 to UD v2.

See http://universaldependencies.org/v2/summary.html for the description of all UD v2 changes.
IMPORTANT: this code does only SOME of the changes and the output should be checked.

Note that this block is not idempotent, i.e. you should not apply it twice on the same data.
It should be idempotent when skipping the coordination transformations (`skip=coord`).

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
    "name": "flat:name",
    "foreign": "flat",  # "flat:foreign" not needed once we have Foreign=Yes in FEATS
}


class Convert1to2(Block):
    """Block for converting UD v1 to UD v2."""

    def __init__(self, skip='', save_stats=True, **kwargs):
        """Create the Convert1to2 block instance.

        Args:
        skip: comma separated list of transformations to skip. Default=empty string (no skipping).
            possible values are:
            upos, upos_copula, deprel_simple, neg, nmod, feats,
            remnants, goeswith, flat, fixed, appos, coord, text.
            If you cannot guess their meaning, consult the source code:-(.
        save_stats: store the ToDo statistics overview into `document.misc["todo"]`?
        """
        super().__init__(**kwargs)
        self.stats = collections.Counter()
        self.skip = {k for k in skip.split(',')}
        self.save_stats = save_stats

    def process_tree(self, tree):  # pylint: disable=too-many-branches
        """Apply all the changes on the current tree.

        This method is automatically called on each tree by Udapi.
        After doing tree-scope changes (remnants), it calls `process_node` on each node.
        By overriding this method in subclasses
        you can reuse just some of the implemented changes.
        """
        # node-local edits
        for node in tree.descendants:
            if 'upos' not in self.skip:
                self.change_upos(node)
            if 'upos_copula' not in self.skip:
                self.change_upos_copula(node)
            if 'deprel_simple' not in self.skip:
                self.change_deprel_simple(node)
            if 'neg' not in self.skip:
                self.change_neg(node)
            if 'nmod' not in self.skip:
                self.change_nmod(node)
            if 'feats' not in self.skip:
                self.change_feats(node)

        # semi-local edits: the neighboring nodes should have fixed deprel before running this
        for node in tree.descendants:
            for deprel in ('goeswith', 'flat'):
                if deprel not in self.skip:
                    self.change_headfinal(node, deprel)

        # edits which need access to the whole tree.
        if 'remnants' not in self.skip:
            self.fix_remnants_in_tree(tree)

        # reattach_coordinations() must go after fix_remnants_in_tree()
        # E.g. in "Marie went to Paris and Miriam to Prague",
        # we need to first remove the edge remnant(Marie, Miriam) and add conj(went, Miriam),
        # which allows reattach_coordinations() to change cc(went, and) → cc(Miriam,and).
        if 'coord' not in self.skip:
            for node in tree.descendants:
                self.reattach_coordinations(node)

        # Fix the plain-text sentence stored in the '# text =' comment.
        if 'text' not in self.skip:
            self.fix_text(tree)

    def log(self, node, short_msg, long_msg):
        """Log node.address() + long_msg and add ToDo=short_msg to node.misc."""
        logging.debug('node %s %s: %s', node.address(), short_msg, long_msg)
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

    def change_deprel_simple(self, node):
        """mwe→fixed, dobj→obj, *pass→*:pass, name→flat, foreign→flat+Foreign=Yes."""
        if node.udeprel == 'foreign':
            node.feats['Foreign'] = 'Yes'
        udeprel, sdeprel = node.udeprel, node.sdeprel
        try:
            node.deprel = DEPREL_CHANGE[udeprel]
        except KeyError:
            return
        if sdeprel:
            if ':' in node.deprel:
                self.log(node, 'deprel', 'deprel=%s:%s new_deprel=%s but %s is lost' %
                         (udeprel, sdeprel, node.deprel, sdeprel))
            else:
                node.deprel += ':' + sdeprel

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

            if node.upos in ['ADV', 'PART', 'AUX']:
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
        if node.upos in ["VERB", "AUX", "ADV"]:
            return 'no'
        # check whether the node is a predicate
        # (either has a nsubj/csubj dependendent or a copula dependent)
        has_cop = any("subj" in child.deprel or child.deprel == 'cop' for child in node.children)
        # Adjectives are very likely complements of copula verbs.
        if node.upos == "ADJ":
            return "no" if has_cop else "maybe"
        # Include NUM for examples such as "one of the guys"
        # and DET for examples such as "some/all of them"
        if node.upos in ["NOUN", "PRON", "PROPN", "NUM", "DET"]:
            return "maybe" if has_cop else "yes"
        return 'maybe'

    def change_nmod(self, node):
        """nmod→obl if parent is not nominal, but predicate."""
        if node.udeprel == 'nmod':
            parent_is_nominal = self.is_nominal(node.parent)
            if parent_is_nominal == 'no':
                node.udeprel = 'obl'
            elif node.deprel == 'nmod:tmod':
                node.deprel = 'obl:tmod'
            elif node.deprel == 'nmod:poss':
                node.deprel = 'nmod:poss'
            elif parent_is_nominal == 'maybe':
                self.log(node, 'nmod', 'deprel=nmod, but parent is ambiguous nominal/predicate')

    def change_feats(self, node):
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

    @staticmethod
    def change_headfinal(node, deprel):
        """deprel=goeswith|flat|fixed|appos must be a head-initial flat structure."""
        if node.udeprel == deprel and node.precedes(node.parent):
            full_deprel = node.deprel
            old_head = node.parent
            all_goeswith = [n for n in old_head.children if n.udeprel == deprel]
            other_children = [n for n in old_head.children if n.udeprel != deprel]
            all_goeswith[0].parent = old_head.parent
            all_goeswith[0].deprel = old_head.deprel
            old_head.deprel = full_deprel
            for a_node in all_goeswith[1:] + other_children + [old_head]:
                a_node.parent = all_goeswith[0]

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

            # Skip also the cases where punct/cc is before the whole coordination.
            # As above, the punct/cc does not belong to the coordination.
            # E.g. "And he is big and strong."
            if node.precedes(conjuncts[0]) and node.precedes(node.parent):
                return

            next_conjunct = next((n for n in conjuncts if node.precedes(n)), None)
            if next_conjunct:
                # Make sure we don't introduce non-projectivities.
                next_sibl = next(n for n in siblings if node.precedes(n) and n.deprel != 'cc')
                if next_sibl != next_conjunct:
                    self.log(node, node.deprel + '-in-coord', 'it may be part of coordination')
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
        'Over 300 Iraqis are reported dead and 500 wounded.' with edges::

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
                root.text = computed
                root.add_comment('ToDoOrigText = ' + stored)
                self.log(root, 'text', 'Sentence string does not agree with the stored text.')

    def after_process_document(self, document):
        """Print overall statistics of ToDo counts."""
        message = 'ud.Convert1to2 ToDo Overview:'
        total = 0
        for todo, count in sorted(self.stats.items(), key=lambda pair: (pair[1], pair[0])):
            total += count
            message += '\n%20s %10d' % (todo, count)
        message += '\n%20s %10d\n' % ('TOTAL', total)
        logging.warning(message)
        if self.save_stats:
            document.meta["todo"] = message
        self.stats.clear()
