"""Block ud.SplitUnderscoreTokens splits tokens with underscores are attaches them using flat.

Usage:
udapy -s ud.SplitUnderscoreTokens < in.conllu > fixed.conllu

Author: Martin Popel
"""
import logging
from udapi.core.block import Block

class SplitUnderscoreTokens(Block):
    """Block for spliting tokens with underscores and attaching them using deprel=flat.

    E.g.::
    1  Hillary_Rodham_Clinton  Hillary_Rodham_ClintonHillary_Rodham_Clinton  NOUN  xpos  0  dep

    is transformed into:
    1  Hillary  Hillary  NOUN  xpos  0 dep
    2  Rodham   Rodham   NOUN  _     1 flat
    3  Clinton  Clinton  NOUN  _     1 flat
    """

    def process_node(self, node):
        if node.form != '_' and '_' in node.form:
            forms = node.form.split('_')
            lemmas = node.lemma.split('_')
            if len(forms) != len(lemmas):
                logging.warning("Different number of underscores in %s and %s, skipping.",
                                node.form, node.lemma)
                return

            last_node = node
            for form, lemma in zip(forms[1:], lemmas[1:]):
                new_node = node.create_child(form=form, lemma=lemma, upos=node.upos, deprel='flat')
                new_node.shift_after_node(last_node)
                last_node = new_node
            node.form = forms[0]
            node.lemma = lemmas[0]
            if node.misc['SpaceAfter'] == 'No':
                del node.misc['SpaceAfter']
                last_node.misc['SpaceAfter'] = 'No'
