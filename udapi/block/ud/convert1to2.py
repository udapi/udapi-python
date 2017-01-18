"""Block Convert1to2 for converting UD v1 to UD v2.

See http://universaldependencies.org/v2/summary.html for the description of all UD v2 changes.
IMPORTANT: this code does only SOME of the changes and the output should be checked.

Author: Martin Popel, based on
https://github.com/UniversalDependencies/tools/tree/master/v2-conversion
by Sebastian Schuster.
"""
import logging

from udapi.core.block import Block

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

    def process_node(self, node):
        """Apply all the changes on the current node.

        This method is automatically called on each node by Udapi.
        By overriding this method in subclasses
        you can reuse just some of the implemented changes.
        """
        self.change_upos(node)
        self.change_deprel_simple(node)
        self.change_neg(node)
        self.change_nmod(node)
        self.change_feat(node)
        self.reattach_coordinations(node)

    @staticmethod
    def log(node, short_msg, long_msg):
        """Log node.address() + long_msg and add ToDo=short_msg to node.misc."""
        logging.warning('node %s: %s', node.address(), long_msg)
        if node.misc['ToDo']:
            node.misc['ToDo'] += ',' + short_msg
        else:
            node.misc['ToDo'] = short_msg

    @staticmethod
    def change_upos(node):
        """CONJ→CCONJ."""
        if node.upos == "CONJ":
            node.upos = "CCONJ"

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
        """neg→advmod/det/ToDo + Polarity=Neg."""
        # TODO: Is this specific for English?
        if node.deprel == 'neg':
            if 'Neg' not in node.feats['PronType']:
                node.feats['Polarity'] = 'Neg'
            if node.upos in ['ADV', 'PART']:
                node.deprel = 'advmod'
            elif node.upos == 'DET':
                node.deprel = 'det'
            else:
                self.log(node, 'neg', 'deprel=neg upos=%s' % node.upos)

    @staticmethod
    def is_nominal(node):
        """Returns 'no' (for predicates), 'yes' (sure nominals) or 'maybe'."""
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
        """Negative→Polarity, Aspect=Pro→Prosp, VerbForm=Trans→Conv, Definite=Red→Cons."""
        if node.feats['Negative']:
            node.feats['Polarity'] = node.feats['Negative']
            del node.feats['Negative']
        if node.feats['Aspect'] == 'Pro':
            node.feats['Aspect'] = 'Prosp'
        if node.feats['VerbForm'] == 'Trans':
            node.feats['VerbForm'] = 'Conv'
        if node.feats['Definite'] == 'Red':
            node.feats['Definite'] = 'Cons'
        if node.feats['Tense'] == 'Nar':
            self.log(node, 'nar', 'Tense=Nar not allowed in UD v2')
        if node.feats['NumType'] == 'Gen':
            self.log(node, 'gen', 'NumType=Gen not allowed in UD v2')

    def reattach_coordinations(self, node):
        """cc and punct in coordinations should depend on the immediately following conjunct."""
        if node.deprel in ['cc', 'punct']:
            conjuncts = [n for n in node.parent.children if n.deprel == 'conj']
            # Skip cases when punct is used outside of coordination
            # and when cc is used without any conj sibling, e.g. "And then we left."
            # Both of these cases are allowed by the UDv2 specification.
            if not conjuncts:
                return
            next_conjunct = next((n for n in conjuncts if node.precedes(n)), None)
            if next_conjunct:
                if node.deprel == 'punct' and node.lemma not in [',', ';']:
                    pass
                else:
                    node.parent = next_conjunct
            elif node.deprel == 'cc':
                self.log(node, 'cc', 'cc with no following conjunct')
