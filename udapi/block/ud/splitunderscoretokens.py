"""Block ud.SplitUnderscoreTokens splits tokens with underscores are attaches them using flat.

Usage:
udapy -s ud.SplitUnderscoreTokens < in.conllu > fixed.conllu

Author: Martin Popel
"""
import logging
from udapi.core.block import Block


class SplitUnderscoreTokens(Block):
    """Block for spliting tokens with underscores and attaching the new nodes using deprel=flat.

    E.g.::
    1  Hillary_Rodham_Clinton  Hillary_Rodham_Clinton  PROPN  xpos  0  dep

    is transformed into:
    1  Hillary  Hillary  PROPN  xpos  0 dep
    2  Rodham   Rodham   PROPN  xpos  1 flat
    3  Clinton  Clinton  PROPN  xpos  1 flat

    Real-world use cases: UD_Irish (`default_deprel=fixed`) and UD_Czech-CLTT v1.4.
    """

    def __init__(self, deprel=None, default_deprel='flat', **kwargs):
        """Create the SplitUnderscoreTokens block instance.

        Args:
        deprel: Which deprel to always use for the newly created nodes?
            Most common values are: flat, fixed, compound. Default=None.
        default_deprel: Which deprel to use for the newly created nodes if the heuristics
            in `deprel_for()` method fail. Default=flat.
        """
        super().__init__(**kwargs)
        self.deprel = deprel
        self.default_deprel = default_deprel

    def process_node(self, node):
        if node.form != '_' and '_' in node.form:
            forms = node.form.split('_')
            lemmas = node.lemma.split('_')
            if len(forms) != len(lemmas):
                logging.warning("Different number of underscores in %s and %s, skipping.",
                                node.form, node.lemma)
                return

            last_node = node
            deprel = self.deprel_for(node)
            for form, lemma in zip(forms[1:], lemmas[1:]):
                new_node = node.create_child(form=form, lemma=lemma, upos=node.upos,
                                             xpos=node.xpos, deprel=deprel)
                new_node.shift_after_node(last_node)
                last_node = new_node
            node.form = forms[0]
            node.lemma = lemmas[0]
            if node.misc['SpaceAfter'] == 'No':
                del node.misc['SpaceAfter']
                last_node.misc['SpaceAfter'] = 'No'

    def deprel_for(self, node):
        """Return deprel of the newly created nodes: `flat`, `fixed`, `compound` or its subtypes.

        See http://universaldependencies.org/u/dep/flat.html
        http://universaldependencies.org/u/dep/fixed.html
        http://universaldependencies.org/u/dep/compound.html
        Note that unlike the first two, `deprel=compound` does not need to be head-initial.

        This method implements a coarse heuristic rules to decide between `fixed` and `flat`.
        """
        if self.deprel:
            return self.deprel

        # Proper names tend to form `flat` constructions.
        if node.upos == 'PROPN':
            return 'flat'

        # Closed-class words (except NUM) tend to form `fixed` constructions.
        if node.upos in ('ADP', 'AUX', 'CCONJ', 'DET', 'PART', 'PRON', 'SCONJ'):
            return 'fixed'

        # The default default :-) is `flat`.
        return self.default_deprel
