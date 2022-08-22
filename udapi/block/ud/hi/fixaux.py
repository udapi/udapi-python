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
        # baiṭha (to sit), uṭha (to rise), rakha (to keep), ā (to come), lā (to bring),
        # pahuñc (to reach), dekh (to look), phar (to return), cal (to walk),
        # caṛh (to climb), saṛ (to rot), nikāl (to remove), girā (to drop), samā
        # (to encounter), dhamaka (to bully).
        # There are also jā (to go) and paṛa (to fall) but we do not list them here
        # because they can also act as genuine auxiliaries.
        hicompound = ['ले', 'दे', 'डाल', 'फेंक', 'बैठ', 'उठ', 'रख', 'आ', 'पहुंच', 'चल', 'निकाल', 'गिरा', 'समा', 'धमक']
        urcompound = ['لے', 'دے', 'ڈال', 'پھینک', 'بیٹھ', 'اٹھ', 'رکھ', 'آ', 'لا', 'پہنچ', 'دیکھ', 'پھر', 'چل', 'چڑھ', 'سڑ']
        recompound = r'^(' + '|'.join(hicompound + urcompound) + r')$'
        # Control and raising verbs.
        # चाहना چاہنا (cāhnā) “to want, to wish” is a control verb but not an auxiliary.
        # Its form چاہیئے (cāhie) “should, ought to” (literally "is wanted"?) is treated as a separate, derived word, and it is a modal auxiliary.
        # दिखाना دکھانا (dikhānā) “to show”
        # बनना بننا (bananā) “to become”
        hiphase = ['लग', 'चुक', 'चाह', 'दिखा', 'बन']
        urphase = ['لگ', 'چک', 'چاہ', 'دکھا', 'بن']
        rephase = r'^(' + '|'.join(hiphase + urphase) + r')$'
        if re.match(recompound, node.lemma) and node.upos == 'AUX' and node.udeprel == 'aux':
            node.deprel = 'compound'
            # The word is no longer treated as an auxiliary, so it should be VERB rather than AUX.
            node.upos = "VERB"
        # वाला والا (vālā) with infinitive is annotated as auxiliary but it should not.
        # It is not even a verb (it does not have a verbal paradigm); it is more
        # like an adjective morphologically, and like a noun syntactically. It means
        # “the one who does the action of the content verb infinitive.”
        # Some occurrences in the original annotation are case or mark, so we do not
        # check AUX/aux here.
        elif node.lemma == 'वाला' or node.lemma == 'والا':
            node.upos = 'ADJ'
            node.feats['AdpType'] = ''
            node.feats['VerbForm'] = ''
            node.feats['Aspect'] = ''
            node.deprel = 'compound'
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
            # آنے is the oblique infinitive form of “to come”
            if node.lemma == 'آنہ':
                node.lemma = 'آ'
            # بنانا बनाना “make, create, produce, cause to be/become”
            # (I don't know why in some instances بنا was used as lemma for کر “to do”.)
            if node.form == 'کر' and node.lemma == 'بنا':
                node.lemma = 'کر'
            # چاہئے (cāhie) “should, ought to” occurs with alternative spellings (should they also be labeled as typos?)
            if node.form == 'چاہئے' or node.form == 'چاہیئے' or node.form == 'چاہیے':
                node.lemma = 'چاہئے'
            if node.form == 'چاہئیں':
                node.lemma = 'چاہئے'
                node.feats['Number'] = 'Plur'
            # چاہے seems to be a wrong lemma of چاہیں_گے “would like”
            if node.lemma == 'چاہے':
                node.lemma = 'چاہ'
            # चुका چکا is a perfective participle of चुकना چکنا (cuknā) “to be finished”
            if node.lemma == 'चुका':
                node.lemma = 'चुक'
            if node.lemma == 'چکا':
                node.lemma = 'چک'
            # दिया دیا is a perfective participle of देना دینا (denā) “to give”
            if node.lemma == 'दिया':
                node.lemma = 'दे'
            if node.lemma == 'دیا' or node.lemma == 'دی' or node.lemma == 'دیت':
                node.lemma = 'دے'
            # دکھائیں (dikhānā) “to show”
            if node.form == 'دکھائیں':
                node.lemma = 'دکھا'
            # گا, گی, گے denote the future tense. They are written as separate
            # words in Urdu (while they are just suffixes in Hindi). However,
            # when written as a separate auxiliary, all these forms should share
            # the same lemma.
            if node.lemma == 'گی' or node.lemma == 'گے':
                node.lemma = 'گا'
            # گیا is a perfective participle of जाना جانا‎ (jānā) “to go”
            # जान جان is nonsense. It occurs with forms like جانی, which is a feminine form of the infinitive جانا‎.
            if node.lemma == 'जाना' or node.lemma == 'जान':
                node.lemma = 'जा'
            if node.lemma == 'گیا' or node.lemma == 'جائے' or node.lemma == 'جاتا' or node.lemma == 'جاتی' or node.lemma == 'جان' or node.lemma == 'جانا' or node.lemma == 'جاؤ' or node.lemma == 'جائی' or node.lemma == 'جاتے' or node.lemma == 'جات':
                node.lemma = 'جا'
            # Wrongly lemmatized present forms of “to be”.
            # In one instance, ہے had a lemma from a neighboring verb, so we also look at the form.
            if node.lemma == 'हों':
                node.lemma = 'है'
            if node.lemma == 'ہوں' or node.lemma == 'ہوا' or node.form == 'ہے':
                node.lemma = 'ہے'
            # लिया لیا is a perfective participle of लेना لینا (lenā) “to take”
            # In one instance, لیا had a lemma from a neighboring verb, so we also look at the form.
            if node.lemma == 'लिया':
                node.lemma = 'ले'
            if node.lemma == 'لیا' or node.form == 'لیا' or node.lemma == 'لو' or node.lemma == 'لی' or node.lemma == 'لیجیے':
                node.lemma = 'لے'
            # लगा لگا is a perfective participle of लगना لگنا (lagnā) “to seem, to appear”
            if node.lemma == 'लगा':
                node.lemma = 'लग'
            if node.lemma == 'لگا':
                node.lemma = 'لگ'
            # پڑے is a perfective participle of پڑنا (paṛnā) “to fall”
            if node.lemma == 'پڑے':
                node.lemma = 'پڑ'
            # پھرے is a perfective participle of پھرنا (pharnā) “to return”
            if node.lemma == 'پھرے':
                node.lemma = 'پھر'
            # रहा رہا is a perfective participle of रहना رہنا (rahnā) “to stay”
            if node.lemma == 'रहा' or node.lemma == 'रहूं':
                node.lemma = 'रह'
            if node.lemma == 'رہا' or node.lemma == 'رہی' or node.lemma == 'رہے':
                node.lemma = 'رہ'
            # sakna to be able to
            if node.lemma == 'سکے' or node.lemma == 'سکی' or node.lemma == 'سکتا' or node.lemma == 'سکت':
                node.lemma = 'سک'
            # Wrongly lemmatized past forms of “to be”.
            if node.lemma == 'थी':
                node.lemma = 'था'
            if node.lemma == 'تھ' or node.lemma == 'تھے' or node.lemma == 'تھیں':
                node.lemma = 'تھا'
            # उठा اٹھا is a perfective participle of उठना اٹھنا (uṭhnā) “to rise, get up”
            if node.lemma == 'उठा':
                node.lemma = 'उठ'
            if node.lemma == 'اٹھا':
                node.lemma = 'اٹھ'
            # The compound part vālā is not an auxiliary. We handle it in process_node()
            # but it must be lemmatized properly.
            if node.lemma == 'والی':
                node.lemma = 'والا'
            # The postposition ke after a verbal stem is not an auxiliary.
            # Example: علحدہ علحدہ کیس رجسٹر کر کے “by registering separate cases”
            if node.lemma == 'کا' and node.form == 'کے':
                node.upos = 'ADP'
                node.deprel = 'mark'
