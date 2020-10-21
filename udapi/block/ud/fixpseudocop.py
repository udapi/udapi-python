"""Block to fix annotation of verbs that are currently treated as copulas
   but they should be treated as normal verbs (with secondary predication)
   instead."""
from udapi.core.block import Block
import logging
import re

class FixPseudoCop(Block):

    def __init__(self, lemma, **kwargs):
        """Create the ud.FixPseudoCop block instance.

        Args:
        lemma: the lemma of the pseudocopula that should be fixed
        """
        super().__init__(**kwargs)
        self.lemma = lemma

    def process_node(self, node):
        pseudocop = self.lemma
        if node.lemma == pseudocop and node.udeprel == "cop":
            secpred = node.parent
            grandparent = secpred.parent
            node.parent = grandparent
            node.deprel = secpred.deprel
            secpred.parent = node
            secpred.deprel = "xcomp"
            ###!!! We should also take care of DEPS if they exist.
            # As a copula, the word was tagged AUX. Now it should be VERB.
            node.upos = "VERB"
            # Examine the children of the original parent.
            # Those that modify the clause should be re-attached to me.
            # Those that modify the word (noun, adjective) should stay there.
            for c in secpred.children:
                # obl is borderline. It could modify an adjective rather than a clause.
                # obj and iobj should not occur in copular clauses but it sometimes
                # occurs with pseudocopulas: "I declare him handsome."
                if re.match("(nsubj|csubj|advmod|advcl|obj|iobj|obl|aux|mark|punct|cc|expl|dislocated|vocative|discourse|parataxis)", c.udeprel):
                    c.parent = node
