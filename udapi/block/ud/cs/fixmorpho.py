"""
A Czech-specific block to fix lemmas, UPOS and morphological features in UD.
It should increase consistency across the Czech treebanks. It focuses on
individual closed-class verbs (such as the auxiliary "být") or on entire classes
of words (e.g. whether or not nouns should have the Polarity feature). It was
created as part of the Hičkok project (while importing nineteenth-century Czech
data) but it should be applicable on any other Czech treebank.
"""
from udapi.core.block import Block
import logging
import re

class FixMorpho(Block):

    def process_node(self, node):
        # Do not touch words marked as Foreign or Typo. They may not behave the
        # way we expect in Czech data.
        if node.feats['Foreign'] == 'Yes' or node.feats['Typo'] == 'Yes':
            return
        # Nouns do not have polarity but the Prague-style tagsets may mark it.
        if node.upos in ['NOUN', 'PROPN']:
            if node.feats['Polarity'] == 'Pos':
                node.feats['Polarity'] = ''
            elif node.feats['Polarity'] == 'Neg':
                logging.warn(f'To remove Polarity=Neg from the NOUN {node.form}, we may have to change its lemma ({node.lemma}).')
        # Clitic forms of personal pronouns have Variant=Short if there is also a longer, full form.
        if node.upos == 'PRON' and node.feats['PronType'] == 'Prs' and re.fullmatch(r'(mi|mě|ti|tě|si|se|ho|mu)', node.form.lower()):
            node.feats['Variant'] = 'Short'
        # Forms of "my" should be lemmatized as "já".
        if node.upos == 'PRON' and node.lemma == 'my':
            node.lemma = 'já'
        # Forms of "vy" should be lemmatized as "ty".
        if node.upos == 'PRON' and node.lemma == 'vy':
            node.lemma = 'ty'
        # Forms of "oni" should be lemmatized as "on" and cases that allow
        # a preposition should have PrepCase.
        if node.upos == 'PRON' and node.lemma in ['on', 'oni']:
            node.lemma = 'on'
            if node.feats['Case'] not in ['Nom', 'Voc']:
                if node.form.lower().startswith('j'):
                    node.feats['PrepCase'] = 'Npr'
                elif re.match(r'[nň]', node.form.lower()):
                    node.feats['PrepCase'] = 'Pre'
        # In 19th century data, the grammaticalized usages of "se", "si" are
        # tagged as PART (rather than a reflexive PRON, which is the standard).
        # Even if it already was tagged PRON, some features may have to be added.
        if node.upos in ['PRON', 'PART'] and node.form.lower() in ['se', 'si']:
            node.lemma = 'se'
            node.upos = 'PRON'
            node.feats['PronType'] = 'Prs'
            node.feats['Reflex'] = 'Yes'
            if node.form.lower() == 'se':
                # Occasionally "se" can be genitive: "z prudkého do se dorážení".
                if not node.feats['Case'] == 'Gen':
                    node.feats['Case'] = 'Acc'
            else:
                node.feats['Case'] = 'Dat'
            node.feats['Variant'] = 'Short'
        # As the genitive/accusative form of "on", "jeho" should have PrepCase.
        if node.upos == 'PRON' and node.form.lower() == 'jeho':
            node.feats['PrepCase'] = 'Npr'
        # Possessive pronouns have Person, Gender[psor] and Number[psor].
        if node.upos == 'DET' and node.feats['Poss'] == 'Yes':
            if node.lemma == 'můj':
                node.feats['Person'] = '1'
                node.feats['Number[psor]'] = 'Sing'
            elif node.lemma == 'tvůj':
                node.feats['Person'] = '2'
                node.feats['Number[psor]'] = 'Sing'
            elif node.lemma == 'náš':
                node.feats['Person'] = '1'
                node.feats['Number[psor]'] = 'Plur'
            elif node.lemma == 'váš':
                node.feats['Person'] = '2'
                node.feats['Number[psor]'] = 'Plur'
            elif node.form.lower() == 'jeho':
                node.feats['Person'] = '3'
                node.feats['Number[psor]'] = 'Sing'
                node.feats['Gender[psor]'] = 'Masc,Neut'
            elif re.fullmatch(r'jich|jejich', node.form.lower()):
                node.lemma = 'jeho'
                node.feats['Person'] = '3'
                node.feats['Number[psor]'] = 'Plur'
        # Reflexive possessive pronoun should not forget the Reflex=Yes feature.
        if node.upos == 'DET' and node.lemma == 'svůj':
            node.feats['Reflex'] = 'Yes'
        # Relative pronoun "jenž" should be PRON, not DET
        # (it inflects for Gender but it can never be used as congruent attribute).
        if node.upos in ['PRON', 'DET'] and node.lemma == 'jenž':
            node.upos = 'PRON'
            if node.form.lower().startswith('j'):
                node.feats['PrepCase'] = 'Npr'
            else:
                node.feats['PrepCase'] = 'Pre'
        # Pronoun "sám" is lemmatized to the long form, it is DET and PronType=Emp.
        if node.upos in ['PRON', 'DET'] and node.lemma == 'sám':
            node.lemma = 'samý'
            node.upos = 'DET'
            node.feats['PronType'] = 'Emp'
            node.feats['Variant'] = 'Short' if re.fullmatch(r'(sám|sama|samo|sami|samy|samu)', node.form.lower()) else ''
        # Pronominal cardinal numerals should be DET, not NUM.
        if node.upos == 'NUM':
            if re.fullmatch(r'(mnoho|málo|několik)', node.lemma):
                node.upos = 'DET'
                node.feats['PronType'] = 'Ind'
                node.feats['NumForm'] = ''
                node.feats['Polarity'] = '' ###!!! so we are losing the distinction mnoho/nemnoho?
            elif re.fullmatch(r'(tolik)', node.lemma):
                node.upos = 'DET'
                node.feats['PronType'] = 'Dem'
                node.feats['NumForm'] = ''
                node.feats['Polarity'] = ''
            elif re.fullmatch(r'(kolik)', node.lemma):
                node.upos = 'DET'
                node.feats['PronType'] = 'Int,Rel'
                node.feats['NumForm'] = ''
                node.feats['Polarity'] = ''
        # Pronominal adverbs have PronType but most of them do not have Degree
        # and Polarity.
        if node.upos == 'ADV':
            if re.fullmatch(r'(tady|tak|tam|teď|tehdy|tu)', node.lemma):
                node.feats['PronType'] = 'Dem'
                node.feats['Degree'] = ''
                node.feats['Polarity'] = ''
            elif re.fullmatch(r'(dokdy|jak|kam|kde|kdy|kudy|odkdy|odkud|proč)', node.lemma):
                node.feats['PronType'] = 'Int,Rel'
                node.feats['Degree'] = ''
                node.feats['Polarity'] = ''
        # In Czech UD, "být" is always tagged as AUX and never as VERB, regardless
        # of the fact that it can participate in purely existential constructions
        # where it no longer acts as a copula. Czech tagsets typically do not
        # distinguish AUX from VERB, which means that converted data may have to
        # be fixed.
        if node.upos == 'VERB' and node.lemma == 'být':
            node.upos = 'AUX'
        # Present forms of perfective verbs normally have Tense=Pres despite
        # meaning future. However, a few imperfective verbs have a separate
        # future form (distinct from present form), which gets Tense=Fut
        # despite inflecting similarly to present forms.
        if node.upos in ['VERB', 'AUX'] and node.feats['Mood'] == 'Ind' and node.feats['Tense'] == 'Pres' and node.feats['Aspect'] != 'Perf' and re.match(r'((bud|půjd|pojed|polez)(u|eš|e|eme?|ete|ou)|polet(ím|íš|í|íme|íte))', node.form.lower()):
            node.feats['Tense'] = 'Fut'
        # "jako" should be SCONJ but 19th century data have it as PART.
        if node.upos == 'PART' and node.lemma == 'jako':
            node.upos = 'SCONJ'
