"""
Block to fix annotation of verbs that are currently treated as auxiliaries
but they should be treated as normal verbs instead.
"""
from udapi.core.block import Block
import logging
import re

class FixAux(Block):

    def process_node(self, node):
        self.fix_lemma(node)
        # The following verbs appear in verb-verb compounds as the semantically
        # less salient element: le (to take), de (to give), ḍāla / phenk (to throw),
        # baiṭha (to sit), uṭha (to rise), rakha (to keep), ā (to come). There
        # are also jā (to go) and paṛa (to fall) but we do not list them here
        # because they can also act as genuine auxiliaries.
        hicompound = ['ले', 'दे', 'डाल', 'बैठ', 'उठ', 'रख', 'आ']
        urcompound = ['لے', 'دے', 'پھینک', 'بیٹھ', 'رکھ', 'آ']
        recompound = r'^(' + '|'.join(hicompound + urcompound) + r')$'
        # Control and raising verbs.
        # چاہنا चाहना (cāhnā) “to want, to wish” is a control verb but not an auxiliary.
        # Its form چاہیئے (cāhie) “should, ought to” (literally "is wanted"?) is treated as a separate, derived word, and it is a modal auxiliary.
        # دکھانا दिखाना (dikhānā) “to show”
        hiphase = ['लग', 'चुक', 'चाह', 'दिखा']
        urphase = ['لگ', 'چک', 'چاہ', 'دکھا']
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

    def fix_lemma(self, node):
        """
        Some verbal forms have wrong lemmas in the Hindi/Urdu treebanks. If they
        are tagged AUX, it means that either the validator fails to recognize a
        correct auxiliary, or we fail here to recognize a spurious auxiliary that
        must be fixed.
        """
        if node.upos == 'AUX':
            # چاہئے (cāhie) “should, ought to” occurs with alternative spellings (should they also be labeled as typos?)
            if node.form == 'چاہئے' or node.form == 'چاہیئے' or node.form == 'چاہیے':
                node.lemma = 'چاہئے'
            if node.form == 'چاہئیں':
                node.lemma = 'چاہئے'
                node.feats['Number'] = 'Plur'
            # گیا is a perfective participle of جانا‎ (jānā) “to go”
            if node.lemma == 'گیا':
                node.lemma = 'جا'
            # لگا is a perfective participle of لگنا (lagnā) “to seem, to appear”
            if node.lemma == 'لگا':
                node.lemma = 'لگ'
            # The postposition ke after a verbal stem is not an auxiliary.
            # Example: علحدہ علحدہ کیس رجسٹر کر کے “by registering separate cases”
            if node.lemma == 'کا' and node.form == 'کے':
                node.upos = 'ADP'
                node.deprel = 'mark'
