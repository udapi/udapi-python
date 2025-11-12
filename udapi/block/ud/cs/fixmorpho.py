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
        #----------------------------------------------------------------------
        # NOUNS, PROPER NOUNS, AND ADJECTIVES
        #----------------------------------------------------------------------
        # Nouns do not have polarity but the Prague-style tagsets may mark it.
        if node.upos in ['NOUN', 'PROPN']:
            if node.feats['Polarity'] == 'Pos':
                node.feats['Polarity'] = ''
            elif node.feats['Polarity'] == 'Neg':
                logging.warn(f'To remove Polarity=Neg from the NOUN {node.form}, we may have to change its lemma ({node.lemma}).')
        # For some nouns, there is disagreement in whether to tag and lemmatize
        # them as proper nouns. We must be careful and not add too many to this
        # rule, as many of them could be used as surnames and then they should
        # be PROPN.
        if node.upos == 'PROPN' and re.fullmatch(r'(bůh|duch|hospodin|město|milost|pán|panna)', node.lemma.lower()):
            node.lemma = node.lemma.lower()
            node.upos = 'NOUN'
        # Lemmatization.
        if node.upos == 'NOUN' and node.lemma == 'zem':
            node.lemma = 'země'
        if node.upos == 'ADJ':
            # Adjectives should be lemmatized to lowercase even if they are part of
            # a multiword name, e.g., "Malá" in "Malá Strana" should be lemmatized
            # to "malý". Exception: Possessive adjectives derived from personal
            # names, e.g., "Karlův".
            if node.feats['Poss'] != 'Yes':
                node.lemma = node.lemma.lower()
            # Short forms of adjectives are rare in Modern Czech and uninflected
            # (they are used as predicates), so they lack the Case feature. But
            # they were inflected for Case in the past, so it is better to add
            # Case=Nom for consistency.
            if node.feats['Variant'] == 'Short' and node.feats['Case'] == '':
                node.feats['Case'] = 'Nom'
        #----------------------------------------------------------------------
        # PRONOUNS AND DETERMINERS
        #----------------------------------------------------------------------
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
        # Although it is questionable, plural possessors are lemmatized to singular
        # possessors in an analogy to personal pronouns: "my" --> "já", "náš" --> "můj".
        # Some source corpora lack Person and [psor] features, others do not respect
        # the lemmatization rule, so in the end we have to look at the forms; but
        # there are potentially many variants, especially in old texts.
        if node.upos == 'DET' and node.feats['Poss'] == 'Yes':
            if node.form.lower().startswith('m'):
                # můj muoj mój mého mému mém mým moje má mojí mé moji mou mí mých mými
                node.feats['Person'] = '1'
                node.feats['Number[psor]'] = 'Sing'
            elif node.form.lower().startswith('t'):
                # tvůj tvuoj tvój tvého tvému tvém tvým tvoje tvá tvojí tvé tvoji tvou tví tvých tvými
                node.feats['Person'] = '2'
                node.feats['Number[psor]'] = 'Sing'
            elif node.form.lower().startswith('n'):
                # náš našeho našemu našem naším naše naší naši našich našim našimi
                node.lemma = 'můj'
                node.feats['Person'] = '1'
                node.feats['Number[psor]'] = 'Plur'
            elif node.form.lower().startswith('v'):
                # váš vašeho vašemu vašem vaším vaše vaší vaši vašich vašim vašimi
                node.lemma = 'tvůj'
                node.feats['Person'] = '2'
                node.feats['Number[psor]'] = 'Plur'
            elif node.form.lower() == 'jeho':
                node.feats['Person'] = '3'
                node.feats['Number[psor]'] = 'Sing'
                if not re.search(r'(Masc|Neut)', node.feats['Gender[psor]']):
                    node.feats['Gender[psor]'] = 'Masc,Neut'
            elif re.fullmatch(r'jehož', node.form.lower()):
                node.lemma = 'jehož'
                node.feats['PronType'] = 'Rel'
                node.feats['Number[psor]'] = 'Sing'
                if not re.search(r'(Masc|Neut)', node.feats['Gender[psor]']):
                    node.feats['Gender[psor]'] = 'Masc,Neut'
            elif node.form.lower() == 'její':
                node.lemma = 'jeho'
                node.feats['Person'] = '3'
                node.feats['Number[psor]'] = 'Sing'
                node.feats['Gender[psor]'] = 'Fem'
            elif re.fullmatch(r'jejíž', node.form.lower()):
                node.lemma = 'jehož'
                node.feats['PronType'] = 'Rel'
                node.feats['Number[psor]'] = 'Sing'
                node.feats['Gender[psor]'] = 'Fem'
            elif re.fullmatch(r'jich|jejich', node.form.lower()):
                node.lemma = 'jeho'
                node.feats['Person'] = '3'
                node.feats['Number[psor]'] = 'Plur'
            elif re.fullmatch(r'jichž|jejichž', node.form.lower()):
                node.lemma = 'jehož'
                node.feats['PronType'] = 'Rel'
                node.feats['Number[psor]'] = 'Plur'
        # Reflexive possessive pronoun should not forget the Reflex=Yes feature.
        if node.upos == 'DET' and node.lemma == 'svůj':
            node.feats['Reflex'] = 'Yes'
        # Demonstrative, interrogative, relative, negative, total and indefinite
        # pronouns (or determiners, because some of them get the DET tag).
        if node.upos in ['PRON', 'DET']:
            # Relative pronoun "jenž" should be PRON, not DET
            # (it inflects for Gender but it can never be used as congruent attribute).
            if node.lemma == 'jenž':
                node.upos = 'PRON'
                if node.form.lower().startswith('j'):
                    node.feats['PrepCase'] = 'Npr'
                else:
                    node.feats['PrepCase'] = 'Pre'
            # Relative pronoun "ješto" should be PRON, not DET (if it is not SCONJ, but that was excluded by a condition above)
            # (it inflects for Gender but it can never be used as congruent attribute).
            elif node.form.lower() == 'ješto':
                node.lemma = 'jenžto'
                node.upos = 'PRON'
                node.feats['PrepCase'] = 'Npr'
            # Pronoun "kdo" is PRON (not DET).
            elif node.lemma == 'kdo':
                node.lemma = 'kdo'
                node.upos = 'PRON'
                if node.feats['PronType'] == '':
                    node.feats['PronType'] = 'Int,Rel'
                # Unlike "co", we annotate "kdo" as Animacy=Anim|Gender=Masc.
                # However, we do not annotate Number ("kdo" can be the subject of a plural verb).
                node.feats['Gender'] = 'Masc'
                node.feats['Animacy'] = 'Anim'
                node.feats['Number'] = ''
            # Pronoun "někdo", "kdosi" is PRON (not DET).
            elif re.fullmatch(r'(kdosi|někdo)', node.lemma):
                node.upos = 'PRON'
                node.feats['PronType'] = 'Ind'
                # Unlike "co", we annotate "kdo" as Animacy=Anim|Gender=Masc.
                # However, we do not annotate Number ("kdo" can be the subject of a plural verb).
                node.feats['Gender'] = 'Masc'
                node.feats['Animacy'] = 'Anim'
                node.feats['Number'] = ''
            # Pronoun "nikdo" is PRON (not DET).
            elif node.lemma == 'nikdo':
                node.lemma = 'nikdo'
                node.upos = 'PRON'
                node.feats['PronType'] = 'Neg'
                # Unlike "co", we annotate "kdo" as Animacy=Anim|Gender=Masc.
                # However, we do not annotate Number ("kdo" can be the subject of a plural verb).
                node.feats['Gender'] = 'Masc'
                node.feats['Animacy'] = 'Anim'
                node.feats['Number'] = ''
            # Pronoun "co" is PRON (not DET).
            elif node.lemma == 'co':
                node.lemma = 'co'
                node.upos = 'PRON'
                if node.feats['PronType'] == '':
                    node.feats['PronType'] = 'Int,Rel'
                # We do not annotate Gender and Number, although it could be argued
                # to be Gender=Neut|Number=Sing.
                node.feats['Gender'] = ''
                node.feats['Animacy'] = ''
                node.feats['Number'] = ''
            # Pronoun "což" is PRON (not DET).
            elif node.lemma == 'což':
                node.lemma = 'což'
                node.upos = 'PRON'
                if node.feats['PronType'] == '':
                    node.feats['PronType'] = 'Rel'
                # We do not annotate Gender and Number, although it could be argued
                # to be Gender=Neut|Number=Sing.
                node.feats['Gender'] = ''
                node.feats['Animacy'] = ''
                node.feats['Number'] = ''
            # Pronoun "něco" is PRON (not DET).
            elif re.fullmatch(r'(cosi|něco)', node.lemma):
                node.upos = 'PRON'
                node.feats['PronType'] = 'Ind'
                # We do not annotate Gender and Number, although it could be argued
                # to be Gender=Neut|Number=Sing.
                node.feats['Gender'] = ''
                node.feats['Animacy'] = ''
                node.feats['Number'] = ''
            # Pronoun "nic" is PRON (not DET).
            elif node.lemma == 'nic':
                node.lemma = 'nic'
                node.upos = 'PRON'
                node.feats['PronType'] = 'Neg'
                # We do not annotate Gender and Number, although it could be argued
                # to be Gender=Neut|Number=Sing.
                node.feats['Gender'] = ''
                node.feats['Animacy'] = ''
                node.feats['Number'] = ''
            # Pronoun "týž" is DET and PronType=Dem.
            elif re.fullmatch(r'(tentýž|týž)', node.lemma):
                node.upos = 'DET'
                node.feats['PronType'] = 'Dem'
            # Pronoun "každý" is DET and PronType=Tot.
            elif node.lemma == 'každý':
                node.upos = 'DET'
                node.feats['PronType'] = 'Tot'
            # Pronoun "vše" is lemmatized to "všechen", it is DET and PronType=Tot.
            elif node.form.lower() == 'vše':
                node.lemma = 'všechen'
                node.upos = 'DET'
                node.feats['PronType'] = 'Tot'
            elif node.lemma == 'všechen':
                node.upos = 'DET'
                node.feats['PronType'] = 'Tot'
            # Pronoun "sám" is lemmatized to the long form, it is DET and PronType=Emp.
            elif node.lemma in ['sám', 'samý']:
                node.lemma = 'samý'
                node.upos = 'DET'
                node.feats['PronType'] = 'Emp'
                node.feats['Variant'] = 'Short' if re.fullmatch(r'(sám|sama|samo|sami|samy|samu)', node.form.lower()) else ''
        #----------------------------------------------------------------------
        # PRONOMINAL NUMERALS AND ADVERBS
        #----------------------------------------------------------------------
        # The numeral "oba" should be NUM, not PRON or DET. But it should have PronType=Tot.
        if node.upos in ['NUM', 'PRON', 'DET'] and node.lemma == 'oba':
            node.upos = 'NUM'
            node.feats['NumType'] = 'Card'
            node.feats['NumForm'] = 'Word'
            node.feats['PronType'] = 'Tot'
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
                if node.feats['PronType'] == '':
                    node.feats['PronType'] = 'Int,Rel'
                node.feats['NumForm'] = ''
                node.feats['Polarity'] = ''
        if node.upos in ['ADV', 'NUM']:
            if re.fullmatch(r'(mnoho|málo|několi)krát', node.lemma):
                node.upos = 'ADV'
                node.feats['NumType'] = 'Mult'
                node.feats['PronType'] = 'Ind'
            elif re.fullmatch(r'(tolikrát)', node.lemma):
                node.upos = 'ADV'
                node.feats['NumType'] = 'Mult'
                node.feats['PronType'] = 'Dem'
            elif re.fullmatch(r'(kolikrát)', node.lemma):
                node.upos = 'ADV'
                node.feats['NumType'] = 'Mult'
                if node.feats['PronType'] == '':
                    node.feats['PronType'] = 'Int,Rel'
        # Pronominal adverbs have PronType but most of them do not have Degree
        # and Polarity.
        if node.upos == 'ADV':
            if re.fullmatch(r'(dosud|nyní|proto|sem|tady|tak|takto|tam|teď|tehdy|tenkrát|tu|zde)', node.lemma):
                node.feats['PronType'] = 'Dem'
                node.feats['Degree'] = ''
                node.feats['Polarity'] = ''
            elif re.fullmatch(r'(dokdy|dokud|jak|kam|kde|kdy|kterak|kudy|odkdy|odkud|proč)', node.lemma):
                if node.feats['PronType'] == '':
                    node.feats['PronType'] = 'Int,Rel'
                node.feats['Degree'] = ''
                node.feats['Polarity'] = ''
            elif re.fullmatch(r'(kdežto)', node.lemma):
                node.feats['PronType'] = 'Rel'
                node.feats['Degree'] = ''
                node.feats['Polarity'] = ''
            elif re.fullmatch(r'(jaksi|kamsi|kdesi|kdysi|kudysi|nějak|někam|někde|někdy|někudy)', node.lemma):
                node.feats['PronType'] = 'Ind'
                node.feats['Degree'] = ''
                node.feats['Polarity'] = ''
            elif re.fullmatch(r'(nijak|nikam|nikde|nikdy|nikudy)', node.lemma):
                node.feats['PronType'] = 'Neg'
                node.feats['Degree'] = ''
                node.feats['Polarity'] = ''
            # Total pronominals can be negated ("nevždy"). Then they get Degree, too.
            elif re.fullmatch(r'(všude|všudy|ve?ždy|ve?ždycky)', node.lemma):
                node.feats['PronType'] = 'Tot'
                node.feats['Degree'] = 'Pos'
                node.feats['Polarity'] = 'Pos'
        #----------------------------------------------------------------------
        # VERBS AND AUXILIARIES
        #----------------------------------------------------------------------
        # In Czech UD, "být" is always tagged as AUX and never as VERB, regardless
        # of the fact that it can participate in purely existential constructions
        # where it no longer acts as a copula. Czech tagsets typically do not
        # distinguish AUX from VERB, which means that converted data may have to
        # be fixed.
        if node.upos == 'VERB' and node.lemma == 'být':
            node.upos = 'AUX'
        if node.upos in ['ADV', 'VERB'] and re.fullmatch(r'(ne)?lze', node.form.lower()):
            node.upos = 'ADV'
            node.lemma = 'lze' # not 'nelze'
            node.feats['VerbForm'] = ''
            node.feats['Voice'] = ''
            node.feats['Aspect'] = ''
            node.feats['Mood'] = ''
            node.feats['Tense'] = ''
            node.feats['Person'] = ''
            node.feats['Number'] = ''
            node.feats['Degree'] = 'Pos'
        if node.upos in ['VERB', 'AUX']:
            # Most non-passive verb forms have Voice=Act, and infinitives should
            # have it, too. Passive infinitives are always periphrastic.
            # (This is not done in the PDT tagset, but we should add it.)
            if node.feats['VerbForm'] == 'Inf':
                node.feats['Voice'] = 'Act'
            # Same for imperatives.
            elif node.feats['Mood'] == 'Imp':
                node.feats['Voice'] = 'Act'
            # Some verbs lack the Aspect feature although they are not biaspectual.
            if node.feats['Aspect'] == '':
                if re.fullmatch(r'(cítit|čekat|činit|číst|dávat|dělat|dít|dívat|hledat|chodit|chtít|jít|kralovat|ležet|milovat|mít|mluvit|moci|mus[ei]t|mysl[ei]t|patřit|počínat|prosit|ptát|působit|sedět|snažit|vědět|vidět|vyprávět|zdát|znamenat|žít)', node.lemma):
                    node.feats['Aspect'] = 'Imp'
                elif re.fullmatch(r'(dát|dojít|dostat|nalézt|napadnout|nechat|obrátit|odpovědět|otevřít|počít|položit|pomoci|poslat|postavit|povědět|poznat|přijít|přinést|říci|učinit|udělat|ukázat|vrátit|vstát|vydat|vzít|začít|zeptat|zůstat)', node.lemma):
                    node.feats['Aspect'] = 'Perf'
                # We must look at word form to distinguish imperfective "stát" from perfective "stát se".
                elif re.fullmatch(r'(stojí(me?|š|te)?|stál(a|o|i|y)?)', node.form.lower()):
                    node.feats['Aspect'] = 'Imp'
                elif re.fullmatch(r'(stan(u|eš|e|eme?|ete|ou)|stal(a|o|i|y)?)', node.form.lower()):
                    node.feats['Aspect'] = 'Perf'
            # Present forms of perfective verbs normally have Tense=Pres despite
            # meaning future. However, a few imperfective verbs have a separate
            # future form (distinct from present form), which gets Tense=Fut
            # despite inflecting similarly to present forms.
            if node.feats['Mood'] == 'Ind' and node.feats['Tense'] == 'Pres' and node.feats['Aspect'] != 'Perf' and re.match(r'((bud|půjd|pojed|polez|pones)(u|eš|e|eme?|ete|ou)|polet(ím|íš|í|íme|íte))', node.form.lower()):
                node.feats['Tense'] = 'Fut'
            # Passive participles (including the short forms) should be ADJ, not VERB.
            # But they keep the verbal features of VerbForm, Voice, Aspect.
            if node.feats['VerbForm'] == 'Part' and node.feats['Voice'] == 'Pass':
                node.upos = 'ADJ'
                # But now we need an adjectival lemma.
                ###!!! Bohužel to občas zahodí normalizaci, kterou tam Martinův tým zavedl ručně, např. "rozhřita" mělo lemma "rozehřát", ale já teď místo "rozehřátý" vyrobím "rozhřitý".
                ###!!! odepříno - odepříný místo odepřený
                ###!!! dovolíno - dovolíný místo dovolený
                ###!!! vyslyšána - vyslyšaný místo vyslyšený
                ###!!! obmezený místo omezený, oslyšaný místo oslyšený
                node.misc['LDeriv'] = node.lemma
                node.lemma = re.sub(r'([nt])[auoiy]?$', r'\1ý', node.form.lower())
                node.lemma = re.sub(r'áný$', r'aný', node.lemma) # ztroskotány --> ztroskotáný --> ztroskotaný; zachován, spořádán
                if node.feats['Polarity'] == 'Neg':
                    node.lemma = re.sub(r'^ne', '', node.lemma)
                if node.feats['Case'] == '':
                    node.feats['Case'] = 'Nom'
                if node.feats['Degree'] == '':
                    node.feats['Degree'] = 'Pos'
                node.feats['Variant'] = 'Short'
        #----------------------------------------------------------------------
        # ADVERBS
        #----------------------------------------------------------------------
        # Words that indicate the speaker's attitude are tagged ADV in UD,
        # although the Czech tagsets often treat them as particles.
        if node.upos == 'PART' and re.fullmatch(r'(asi?|dokonce|jistě|hlavně|hned|možná|opravdu|skoro|skutečně|snad|třeba|určitě|vlastně|vůbec|zajisté|zase|zrovna|zřejmě|zvláště)', node.lemma):
            node.upos = 'ADV'
            node.feats['Degree'] = 'Pos'
            node.feats['Polarity'] = 'Pos'
        # Adverb "brzo" should be lemmatized as "brzy".
        if node.upos == 'ADV' and node.form.lower() == 'brzo':
            node.lemma = 'brzy'
        if node.upos == 'ADV' and node.form.lower() == 'teprv':
            node.lemma = 'teprve'
        # All non-pronominal adverbs (and also some pronominal ones) should
        # have Degree and Polarity. At least for now we also exclude adverbial
        # numerals, e.g. "jednou" – "nejednou".
        if node.upos == 'ADV' and node.feats['PronType'] == '' and node.feats['NumType'] == '':
            if node.feats['Degree'] == '':
                node.feats['Degree'] = 'Pos'
            if node.feats['Polarity'] == '':
                node.feats['Polarity'] = 'Pos'
        #----------------------------------------------------------------------
        # PREPOSITIONS
        #----------------------------------------------------------------------
        # Preposition "u" may combine with Case=Loc|Acc in old texts, and then
        # it functions as a vocalized counterpart of "v". Nevertheless, we always
        # lemmatize it as "u" and thus AdpType is Prep, not Voc.
        if node.upos == 'ADP' and node.form.lower() == 'u':
            node.lemma = 'u'
            node.feats['AdpType'] = 'Prep'
        #----------------------------------------------------------------------
        # PARTICLES THAT SHOULD BE ADVERBS
        #----------------------------------------------------------------------
        # "jako" should be SCONJ but 19th century data have it as PART.
        if node.upos == 'PART' and node.lemma == 'jako':
            node.upos = 'SCONJ'
