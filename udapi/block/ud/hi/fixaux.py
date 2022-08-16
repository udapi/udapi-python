"""
Block to fix annotation of verbs that are currently treated as auxiliaries
but they should be treated as normal verbs instead.
"""
from udapi.core.block import Block
import logging
import re

class FixAux(Block):

    def process_node(self, node):
        # The following verbs appear in verb-verb compounds as the semantically
        # less salient element: le (to take), de (to give), ḍāla (to throw),
        # baiṭha (to sit), uṭha (to rise), rakha (to keep), ā (to come). There
        # are also jā (to go) and paṛa (to fall) but we do not list them here
        # because they can also act as genuine auxiliaries.
        hicompound = ['ले', 'दे', 'डाल', 'बैठ', 'उठ', 'रख', 'आ']
        urcompound = ['لے', 'دے', 'بیٹھ', 'رکھ', 'آ']
        recompound = r'^(' + '|'.join(hicompound + urcompound) + r')$'
        hiphase = ['लग', 'चुक']
        urphase = ['لگ', 'چک']
        rephase = r'^(' + '|'.join(hiphase + urphase) + r')$'
        if re.match(recompound, node.lemma) and node.upos == 'AUX' and node.udeprel == 'aux':
            node.deprel = 'compound'
            # The word is no longer treated as an auxiliary, so it should be VERB rather than AUX.
            node.upos = "VERB"
        elif re.match(rephase, node.lemma) and node.upos == 'AUX' and node.udeprel == 'aux':
            secpred = node.parent
            grandparent = secpred.parent
            node.parent = grandparent
            node.deprel = secpred.deprel
            secpred.parent = node
            secpred.deprel = "xcomp"
            ###!!! We should also take care of DEPS if they exist.
            # The word is no longer treated as an auxiliary, so it should be VERB rather than AUX.
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