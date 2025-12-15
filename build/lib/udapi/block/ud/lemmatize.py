"""Block to add missing lemmas in cases where it seems obvious what the lemma should be."""
from udapi.core.block import Block
import logging
import re

class Lemmatize(Block):

    def process_node(self, node):
        """
        Some treebanks lack lemmas for some or all words. Occasionally we may be
        able to guess that the lemma is identical to the word form. This block
        will then fill out the lemma.

        For some parts of speech, we can only say that the form is the lemma if
        we have morphological features that will confirm it is the right form.
        """
        if node.lemma == '' or node.lemma == '_' and node.form != '_' and node.feats['Typo'] != 'Yes':
            # Many closed classes do not inflect and have the same lemma as the form (just lowercased).
            if re.match(r'^(PUNCT|SYM|ADP|CCONJ|SCONJ|PART|INTJ|X)$', node.upos):
                node.lemma = node.form.lower()
            # NOUN PROPN ADJ PRON DET NUM VERB AUX ADV
            # ADV: use positive affirmative
            elif re.match(r'^(ADV)$', node.upos) and re.match(r'^(Pos)?$', node.feats['Degree']) and re.match(r'^(Pos)?$', node.feats['Polarity']):
                node.lemma = node.form.lower()
            # VERB and AUX: use the infinitive
            elif re.match(r'^(VERB|AUX)$', node.upos) and node.feats['VerbForm'] == 'Inf' and re.match(r'^(Pos)?$', node.feats['Polarity']):
                node.lemma = node.form.lower()
            # NOUN and PROPN: use singular nominative (but do not lowercase for PROPN)
            # Note: This rule is wrong in German, where no nouns should be lowercased.
            elif re.match(r'^(NOUN)$', node.upos) and re.match(r'^(Sing)?$', node.feats['Number']) and re.match(r'^(Nom)?$', node.feats['Case']) and re.match(r'^(Pos)?$', node.feats['Polarity']):
                node.lemma = node.form.lower()
            elif re.match(r'^(PROPN)$', node.upos) and re.match(r'^(Sing)?$', node.feats['Number']) and re.match(r'^(Nom)?$', node.feats['Case']) and re.match(r'^(Pos)?$', node.feats['Polarity']):
                node.lemma = node.form
            # ADJ: use masculine singular nominative positive affirmative
            elif re.match(r'^(ADJ)$', node.upos) and re.match(r'^(Masc)?$', node.feats['Gender']) and re.match(r'^(Sing)?$', node.feats['Number']) and re.match(r'^(Nom)?$', node.feats['Case']) and re.match(r'^(Pos)?$', node.feats['Degree']) and re.match(r'^(Pos)?$', node.feats['Polarity']):
                node.lemma = node.form.lower()
            # ADJ, PRON, DET: use masculine singular nominative (pronouns: each person has its own lemma)
            elif re.match(r'^(ADJ|PRON|DET)$', node.upos) and re.match(r'^(Masc)?$', node.feats['Gender']) and re.match(r'^(Sing)?$', node.feats['Number']) and re.match(r'^(Nom)?$', node.feats['Case']):
                node.lemma = node.form.lower()
            # NUM: use masculine nominative (number, if present at all, is lexical)
            elif re.match(r'^(NUM)$', node.upos) and re.match(r'^(Masc)?$', node.feats['Gender']) and re.match(r'^(Nom)?$', node.feats['Case']):
                node.lemma = node.form.lower()
