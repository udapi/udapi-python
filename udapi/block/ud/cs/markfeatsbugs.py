"""
Block to identify missing or ill-valued features in Czech. Any bugs that it
finds will be saved in the MISC column as a Bug attribute, which can be later
used in filters and highlighted in text output.

Usage: cat *.conllu | udapy -HAMX layout=compact ud.cs.MarkFeatsBugs > bugs.html
Windows: python udapy read.Conllu files="a.conllu,b.conllu" merge=1 ud.cs.MarkFeatsBugs write.TextModeTreesHtml files="bugs.html" marked_only=1 layout=compact attributes=form,lemma,upos,xpos,feats,deprel,misc
"""
import udapi.block.ud.markfeatsbugs
import logging
import re

class MarkFeatsBugs(udapi.block.ud.markfeatsbugs.MarkFeatsBugs):

    # The convention used in PDT is not consistent. Adjectives are fully disambiguated
    # (three genders, two animacies, three numbers, seven cases), even though some
    # forms are shared among many feature combinations. On the other hand, pronouns
    # and determiners omit some features in the context of certain values of other
    # features (e.g., gender and animacy are not distinguished in plural if the case
    # is genitive, dative, locative or instrumental).
    # In contrast, ČNK (CNC) fully disambiguates pronouns and determiners just like
    # adjectives.
    # Here we can trigger one of the two conventions. It should become a block parameter
    # in the future.
    pdt20 = False # True = like in PDT 2.0; False = like in ČNK

    def process_node(self, node):
        # Czech constraints should not be applied to foreign words.
        if node.feats['Foreign'] == 'Yes':
            pass
        # NOUNS ################################################################
        elif node.upos == 'NOUN':
            self.check_required_features(node, ['Gender', 'Number', 'Case', 'Polarity'])
            if node.feats['VerbForm'] == 'Vnoun':
                # verbal nouns: bytí, dělání, ...
                self.check_allowed_features(node, {
                    'VerbForm': ['Vnoun'],
                    'Gender': ['Neut'],
                    'Number': ['Sing', 'Dual', 'Plur'],
                    'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                    'Polarity': ['Pos', 'Neg'],
                    'Foreign': ['Yes']
                })
            elif node.feats['Gender'] == 'Masc':
                self.check_required_features(node, ['Animacy'])
                self.check_allowed_features(node, {
                    'Gender': ['Masc', 'Fem', 'Neut'],
                    'Animacy': ['Anim', 'Inan'],
                    'Number': ['Sing', 'Dual', 'Plur'],
                    'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                    'Polarity': ['Pos', 'Neg'],
                    'Foreign': ['Yes']})
            else:
                self.check_allowed_features(node, {
                    'Gender': ['Masc', 'Fem', 'Neut'],
                    'Number': ['Sing', 'Dual', 'Plur'],
                    'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                    'Polarity': ['Pos', 'Neg'],
                    'Foreign': ['Yes']})
        # PROPER NOUNS #########################################################
        elif node.upos == 'PROPN':
            self.check_required_features(node, ['Gender', 'Number', 'Case', 'Polarity'])
            if node.feats['Gender'] == 'Masc':
                self.check_required_features(node, ['Animacy'])
                self.check_allowed_features(node, {
                    'Gender': ['Masc', 'Fem', 'Neut'],
                    'Animacy': ['Anim', 'Inan'],
                    'Number': ['Sing', 'Dual', 'Plur'],
                    'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                    'Polarity': ['Pos', 'Neg'],
                    'NameType': ['Giv', 'Sur', 'Geo'],
                    'Foreign': ['Yes']})
            else:
                self.check_allowed_features(node, {
                    'Gender': ['Masc', 'Fem', 'Neut'],
                    'Number': ['Sing', 'Dual', 'Plur'],
                    'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                    'Polarity': ['Pos', 'Neg'],
                    'NameType': ['Giv', 'Sur', 'Geo'],
                    'Foreign': ['Yes']})
        # ADJECTIVES ###########################################################
        elif node.upos == 'ADJ':
            if node.feats['Poss'] == 'Yes': # possessive adjectives
                if node.feats['Gender'] == 'Masc':
                    self.check_required_features(node, ['Poss', 'Gender[psor]', 'Gender', 'Animacy', 'Number', 'Case'])
                    self.check_allowed_features(node, {
                        'Poss': ['Yes'],
                        'Gender[psor]': ['Masc', 'Fem'],
                        'Gender': ['Masc', 'Fem', 'Neut'],
                        'Animacy': ['Anim', 'Inan'],
                        'Number': ['Sing', 'Dual', 'Plur'],
                        'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                        'NameType': ['Giv', 'Sur'], # for possessive adjectives derived from personal names
                        'Foreign': ['Yes']})
                else:
                    self.check_required_features(node, ['Poss', 'Gender[psor]', 'Gender', 'Number', 'Case'])
                    self.check_allowed_features(node, {
                        'Poss': ['Yes'],
                        'Gender[psor]': ['Masc', 'Fem'],
                        'Gender': ['Masc', 'Fem', 'Neut'],
                        'Number': ['Sing', 'Dual', 'Plur'],
                        'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                        'NameType': ['Giv', 'Sur'], # for possessive adjectives derived from personal names
                        'Foreign': ['Yes']})
            elif node.feats['NumType'] == 'Ord': # ordinal numerals are a subtype of adjectives
                if node.feats['Gender'] == 'Masc':
                    self.check_required_features(node, ['NumType', 'Gender', 'Animacy', 'Number', 'Case'])
                    self.check_allowed_features(node, {
                        'NumType': ['Ord'],
                        'Gender': ['Masc', 'Fem', 'Neut'],
                        'Animacy': ['Anim', 'Inan'],
                        'Number': ['Sing', 'Dual', 'Plur'],
                        'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                        'Foreign': ['Yes']})
                else:
                    self.check_required_features(node, ['NumType', 'Gender', 'Number', 'Case'])
                    self.check_allowed_features(node, {
                        'NumType': ['Ord'],
                        'Gender': ['Masc', 'Fem', 'Neut'],
                        'Number': ['Sing', 'Dual', 'Plur'],
                        'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                        'Foreign': ['Yes']})
            elif node.feats['VerbForm'] == 'Part': # participles (except l-participles) are a subtype of adjectives
                self.check_required_features(node, ['VerbForm', 'Voice'])
                if node.feats['Voice'] == 'Act': # active participles have tense, passives don't
                    if node.feats['Gender'] == 'Masc':
                        self.check_required_features(node, ['VerbForm', 'Aspect', 'Voice', 'Tense', 'Gender', 'Animacy', 'Number', 'Case', 'Polarity'])
                        self.check_allowed_features(node, {
                            'VerbForm': ['Part'],
                            'Aspect': ['Imp', 'Perf'],
                            'Voice': ['Act'],
                            'Tense': ['Past', 'Pres', 'Fut'], # Fut only for lemma 'boudoucí'
                            'Gender': ['Masc', 'Fem', 'Neut'],
                            'Animacy': ['Anim', 'Inan'],
                            'Number': ['Sing', 'Dual', 'Plur'],
                            'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                            'Polarity': ['Pos', 'Neg'],
                            'Variant': ['Short'],
                            'Foreign': ['Yes']})
                    else:
                        self.check_required_features(node, ['VerbForm', 'Aspect', 'Voice', 'Tense', 'Gender', 'Number', 'Case', 'Polarity'])
                        self.check_allowed_features(node, {
                            'VerbForm': ['Part'],
                            'Aspect': ['Imp', 'Perf'],
                            'Voice': ['Act'],
                            'Tense': ['Past', 'Pres', 'Fut'], # Fut only for lemma 'boudoucí'
                            'Gender': ['Masc', 'Fem', 'Neut'],
                            'Number': ['Sing', 'Dual', 'Plur'],
                            'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                            'Polarity': ['Pos', 'Neg'],
                            'Variant': ['Short'],
                            'Foreign': ['Yes']})
                else:
                    if node.feats['Gender'] == 'Masc':
                        self.check_required_features(node, ['VerbForm', 'Aspect', 'Voice', 'Gender', 'Animacy', 'Number', 'Case', 'Polarity'])
                        self.check_allowed_features(node, {
                            'VerbForm': ['Part'],
                            'Aspect': ['Imp', 'Perf'],
                            'Voice': ['Pass'],
                            'Gender': ['Masc', 'Fem', 'Neut'],
                            'Animacy': ['Anim', 'Inan'],
                            'Number': ['Sing', 'Dual', 'Plur'],
                            'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                            'Polarity': ['Pos', 'Neg'],
                            'Variant': ['Short'],
                            'Foreign': ['Yes']})
                    else:
                        self.check_required_features(node, ['VerbForm', 'Aspect', 'Voice', 'Gender', 'Number', 'Case', 'Polarity'])
                        self.check_allowed_features(node, {
                            'VerbForm': ['Part'],
                            'Aspect': ['Imp', 'Perf'],
                            'Voice': ['Pass'],
                            'Gender': ['Masc', 'Fem', 'Neut'],
                            'Number': ['Sing', 'Dual', 'Plur'],
                            'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                            'Polarity': ['Pos', 'Neg'],
                            'Variant': ['Short'],
                            'Foreign': ['Yes']})
            elif node.feats['Variant'] == 'Short': # short (nominal) forms of adjectives have no degree
                if node.feats['Gender'] == 'Masc':
                    self.check_required_features(node, ['Gender', 'Animacy', 'Number', 'Case', 'Polarity', 'Variant'])
                    self.check_allowed_features(node, {
                        'Gender': ['Masc', 'Fem', 'Neut'],
                        'Animacy': ['Anim', 'Inan'],
                        'Number': ['Sing', 'Dual', 'Plur'],
                        'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                        'Polarity': ['Pos', 'Neg'],
                        'Variant': ['Short'],
                        'Foreign': ['Yes']})
                else:
                    self.check_required_features(node, ['Gender', 'Number', 'Case', 'Polarity', 'Variant'])
                    self.check_allowed_features(node, {
                        'Gender': ['Masc', 'Fem', 'Neut'],
                        'Number': ['Sing', 'Dual', 'Plur'],
                        'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                        'Polarity': ['Pos', 'Neg'],
                        'Variant': ['Short'],
                        'Foreign': ['Yes']})
            else: # regular adjectives
                if node.feats['Gender'] == 'Masc':
                    self.check_required_features(node, ['Gender', 'Animacy', 'Number', 'Case', 'Degree', 'Polarity'])
                    self.check_allowed_features(node, {
                        'Gender': ['Masc', 'Fem', 'Neut'],
                        'Animacy': ['Anim', 'Inan'],
                        'Number': ['Sing', 'Dual', 'Plur'],
                        'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                        'Degree': ['Pos', 'Cmp', 'Sup'],
                        'Polarity': ['Pos', 'Neg'],
                        'Foreign': ['Yes']})
                else:
                    self.check_required_features(node, ['Gender', 'Number', 'Case', 'Degree', 'Polarity'])
                    self.check_allowed_features(node, {
                        'Gender': ['Masc', 'Fem', 'Neut'],
                        'Number': ['Sing', 'Dual', 'Plur'],
                        'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                        'Degree': ['Pos', 'Cmp', 'Sup'],
                        'Polarity': ['Pos', 'Neg'],
                        'Foreign': ['Yes']})
        # PRONOUNS #############################################################
        elif node.upos == 'PRON':
            self.check_required_features(node, ['PronType'])
            if node.feats['PronType'] == 'Prs':
                if node.feats['Reflex'] == 'Yes':
                    self.check_required_features(node, ['PronType', 'Reflex', 'Case'])
                    self.check_allowed_features(node, {
                        'PronType': ['Prs'],
                        'Reflex': ['Yes'],
                        'Case': ['Gen', 'Dat', 'Acc', 'Loc', 'Ins'],
                        'Variant': ['Short']
                    })
                else: # not reflexive
                    if node.feats['Person'] == '3': # on, ona, ono, oni, ony
                        if re.match(r'^(Nom|Voc)$', node.feats['Case']): # on, ona, ono, oni, ony
                            self.check_adjective_like(node, ['PronType', 'Person'], {
                                'PronType': ['Prs'],
                                'Person': ['3']
                            })
                        elif node.feats['Variant'] == 'Short': # ho, mu
                            # The short (clitic) forms do not have PrepCase.
                            self.check_adjective_like(node, ['PronType', 'Person'], {
                                'PronType': ['Prs'],
                                'Person': ['3'],
                                'Variant': ['Short']
                            })
                        else: # jeho, něho, jemu, němu, jej, něj, něm, jím, ním, jí, ní, ji, ni, je, ně
                            # Mostly only two gender groups and no animacy:
                            # Masc,Neut ... jeho, jemu, jej, něm, jím
                            # Fem ... jí, ji, ní
                            # Neut ... je
                            # No gender in dual and plural:
                            # Plur ... jich, jim, je, nich, jimi
                            # Here we require PrepCase but disallow Variant.
                            self.check_adjective_like(node, ['PronType', 'Person', 'PrepCase'], {
                                'PronType': ['Prs'],
                                'Person': ['3'],
                                'PrepCase': ['Npr', 'Pre']
                            })
                    else: # 1st and 2nd person do not have gender: já, ty
                        self.check_required_features(node, ['PronType', 'Person', 'Number', 'Case'])
                        self.check_allowed_features(node, {
                            'PronType': ['Prs'],
                            'Person': ['1', '2'],
                            'Number': ['Sing', 'Dual', 'Plur'],
                            'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                            'Variant': ['Short']
                        })
            elif re.search(r'k[dt]o', node.lemma): # kdo (kto), kdož, někdo, nikdo
                # There is no Number. Někdo and nikdo behave like singular;
                # kdo is by default singular as well but it also occurs as a subject
                # of plural verbs.
                self.check_required_features(node, ['PronType', 'Gender', 'Animacy', 'Case'])
                self.check_allowed_features(node, {
                    'PronType': ['Int,Rel', 'Rel', 'Ind', 'Neg'],
                    'Gender': ['Masc'],
                    'Animacy': ['Anim'],
                    'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Loc', 'Ins']
                })
            elif re.match(r'^(co|což|něco|nicož)$', node.lemma):
                # Although these pronouns behave by default as neuter singular,
                # no Gender and Number is annotated. However, quite unusually,
                # there is Animacy=Inan without Gender.
                ###!!! This should probably be fixed in all Czech treebanks and
                ###!!! in Interset. The pronoun should get Gender=Neut and no
                ###!!! animacy. For now, let's at least make animacy an optional
                ###!!! feature (I see that we already do not fill it in the Old
                ###!!! Czech data).
                self.check_required_features(node, ['PronType', 'Case'])
                self.check_allowed_features(node, {
                    'PronType': ['Int,Rel', 'Rel', 'Ind', 'Neg'],
                    'Animacy': ['Inan'],
                    'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Loc', 'Ins']
                })
            elif node.lemma == 'ješto':
                # Unlike 'jenžto', this relative pronoun does not inflect, it
                # always occurs in a nominative position, but the context can
                # be any gender and number.
                self.check_required_features(node, ['PronType', 'Case'])
                self.check_allowed_features(node, {
                    'PronType': ['Rel'],
                    'Case': ['Nom']
                })
            elif re.match(r'^(jenž|jenžto)$', node.lemma):
                # The relative pronouns 'jenž', 'jenžto' inflect for gender;
                # while we normally take this as a sign of DET (instead of PRON),
                # these can never act as real DET because they never modify a
                # nominal.
                # Similarly to the personal pronoun 'on', animacy is only
                # annotated for masculine nominative plural, non-nominative
                # forms are merged for masculine and neuter (jehož, jemuž), and
                # non-singular gender is only annotated in nominative (while
                # these cases are common for all genders: jichž, jimž, jimiž).
                # Unlike 'on', 'jenž' has the feature PrepCase everywhere, even
                # in the nominative, although there is no prepositional counter-
                # part (but similarly the locative has no prepositionless form).
                self.check_adjective_like(node, ['PronType', 'PrepCase'], {
                    'PronType': ['Rel'],
                    'PrepCase': ['Npr', 'Pre']
                })
            else:
                # What remains is the relative pronoun 'an'. It behaves similarly
                # to 'jenž' but it does not have the PrepCase feature and it
                # only occurs in the nominative.
                if node.feats['Gender'] == 'Masc' and node.feats['Number'] == 'Plur': # ani
                    self.check_required_features(node, ['PronType', 'Gender', 'Animacy', 'Number', 'Case'])
                    self.check_allowed_features(node, {
                        'PronType': ['Rel'],
                        'Gender': ['Masc'],
                        'Animacy': ['Anim', 'Inan'],
                        'Number': ['Plur'],
                        'Case': ['Nom']
                    })
                else: # not Masc Plur: an, ana, ano, any
                    self.check_required_features(node, ['PronType', 'Gender', 'Number', 'Case'])
                    self.check_allowed_features(node, {
                        'PronType': ['Rel'],
                        'Gender': ['Masc', 'Fem', 'Neut'],
                        'Number': ['Sing', 'Dual', 'Plur'],
                        'Case': ['Nom']
                    })
        # DETERMINERS ##########################################################
        elif node.upos == 'DET':
            # Possessive determiners 'jeho' and 'jejich' (formerly 'jich') do not inflect, i.e., no Gender, Number, Case.
            # Note that the possessive determiner 'její' (formerly 'jejie') does inflect, although it also has the lemma 'jeho'.
            if re.match(r'^(jeho|jejich|jich)(ž(to)?)?$', node.form.lower()):
                self.check_required_features(node, ['PronType', 'Poss', 'Person', 'Number[psor]'])
                self.check_allowed_features(node, {
                    'PronType': ['Prs', 'Rel'],
                    'Poss': ['Yes'],
                    'Person': ['3'],
                    'Number[psor]': ['Sing', 'Dual', 'Plur'],
                    'Gender[psor]': ['Masc,Neut']
                })
            elif re.match(r'^(její|jejie|jejího|jejieho|jejímu|jejiemu|jejím|jejiem|jejiej|jejíma|jejiema|jejích|jejiech|jejími|jejiemi)(ž(to)?)?$', node.form.lower()):
                # The feminine possessive 'její' slightly inflects, unlike 'jeho' and 'jejich'.
                # Congruent gender is annotated only in singular. Masculine and
                # neuter are merged even in nominative. Feminine singular does
                # not distinguish case in PDT but we need it in Old Czech at
                # least for 'jejiej'.
                if node.feats['Number'] == 'Sing':
                    self.check_required_features(node, ['PronType', 'Poss', 'Person', 'Number[psor]', 'Gender[psor]', 'Gender', 'Number', 'Case'])
                    self.check_allowed_features(node, {
                        'PronType': ['Prs', 'Rel'],
                        'Poss': ['Yes'],
                        'Person': ['3'],
                        'Number[psor]': ['Sing'],
                        'Gender[psor]': ['Fem'],
                        'Gender': ['Masc,Neut', 'Fem'],
                        'Number': ['Sing'],
                        'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins']
                    })
                else:
                    self.check_required_features(node, ['PronType', 'Poss', 'Person', 'Number[psor]', 'Gender[psor]', 'Number', 'Case'])
                    self.check_allowed_features(node, {
                        'PronType': ['Prs', 'Rel'],
                        'Poss': ['Yes'],
                        'Person': ['3'],
                        'Number[psor]': ['Sing'],
                        'Gender[psor]': ['Fem'],
                        'Number': ['Dual', 'Plur'],
                        'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins']
                    })
            elif node.feats['Poss'] == 'Yes': # 'můj', 'tvůj', 'svůj'
                if node.feats['Reflex'] == 'Yes':
                    self.check_adjective_like(node, ['PronType', 'Poss', 'Reflex'], {
                        'PronType': ['Prs'],
                        'Poss': ['Yes'],
                        'Reflex': ['Yes']
                    })
                else:
                    self.check_adjective_like(node, ['PronType', 'Poss', 'Person', 'Number[psor]'], {
                        'PronType': ['Prs'],
                        'Poss': ['Yes'],
                        'Person': ['1', '2'],
                        'Number[psor]': ['Sing', 'Plur']
                    })
            elif re.match(r'^(samý)$', node.lemma):
                # Unlike other determiners, it allows Variant=Short: sám, sama, samu, samo, sami, samy.
                self.check_adjective_like(node, ['PronType'], {'PronType': ['Emp'], 'Variant': ['Short']})
            else:
                self.check_adjective_like(node, ['PronType'], {'PronType': ['Dem', 'Int,Rel', 'Rel', 'Ind', 'Neg', 'Tot']})
        # NUMERALS #############################################################
        elif node.upos == 'NUM':
            self.check_required_features(node, ['NumType', 'NumForm'])
            # Arabic digits and Roman numerals do not have inflection features.
            if re.match(r'^(Digit|Roman)$', node.feats['NumForm']):
                self.check_allowed_features(node, {
                    'NumType': ['Card'],
                    'NumForm': ['Digit', 'Roman']
                })
            else:
                # 'jeden' has Gender, Animacy, Number, Case: jeden, jedna, jedno, jednoho, jednomu, jednom, jedním, jedné, jednu, jednou, jedni, jedny, jedněch, jedněm, jedněmi.
                # 'dva', 'oba' have Gender, Number=Dual(Plur in modern Czech), Case: dva, dvě, dvou, dvěma.
                # 'tři', 'čtyři' have Number=Plur, Case: tři, třech, třem, třemi.
                # 'pět' and more have Number=Plur, Case: pět, pěti.
                if node.lemma == 'jeden':
                    self.check_required_features(node, ['NumType', 'NumForm', 'Number', 'Case'])
                    self.check_allowed_features(node, {
                        'NumType': ['Card'],
                        'NumForm': ['Word'],
                        'Gender': ['Masc', 'Masc,Neut', 'Fem', 'Fem,Neut', 'Neut'], # similarly to determiners, genders are merged in some slots of the paradigm
                        'Animacy': ['Anim', 'Inan'],
                        'Number': ['Sing', 'Dual', 'Plur'],
                        'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins']
                    })
                elif re.match(r'^(dva|oba)$', node.lemma):
                    self.check_required_features(node, ['NumType', 'NumForm', 'Gender', 'Number', 'Case'])
                    if self.pdt20:
                        self.check_allowed_features(node, {
                            'NumType': ['Card'],
                            'NumForm': ['Word'],
                            'Gender': ['Masc', 'Masc,Neut', 'Fem', 'Fem,Neut', 'Neut'], # similarly to determiners, genders are merged in some slots of the paradigm
                            'Number': ['Dual', 'Plur'],
                            'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins']
                        })
                    else:
                        self.check_allowed_features(node, {
                            'NumType': ['Card'],
                            'NumForm': ['Word'],
                            'Gender': ['Masc', 'Fem', 'Neut'],
                            'Animacy': ['Anim', 'Inan'],
                            'Number': ['Dual', 'Plur'],
                            'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins']
                        })
                else:
                    self.check_required_features(node, ['NumType', 'NumForm', 'Number', 'Case'])
                    self.check_allowed_features(node, {
                        'NumType': ['Card'],
                        'NumForm': ['Word'],
                        'Number': ['Plur'],
                        'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins']
                    })
        # VERBS AND AUXILIARIES ################################################
        elif re.match(r'^(VERB|AUX)$', node.upos):
            self.check_required_features(node, ['Aspect', 'VerbForm'])
            if node.feats['VerbForm'] == 'Inf':
                # There is no voice. For some reason, PDT does not annotate that
                # the infinitive form is active (while a passive infinitive is
                # a combination of the infinitive with a passive participle).
                self.check_required_features(node, ['Polarity'])
                self.check_allowed_features(node, {
                    'Aspect': ['Imp', 'Perf'],
                    'VerbForm': ['Inf'],
                    'Polarity': ['Pos', 'Neg']
                })
            elif node.feats['VerbForm'] == 'Fin':
                # Voice is optional. For some reason it is not annotated with
                # imperatives (although passive imperatives are a combination
                # of the active imperative and a passive participle). It is
                # also not annotated at the conditional auxiliary 'bych', 'bys', 'by', 'bychom', 'byste'.
                if node.feats['Mood'] == 'Cnd':
                    self.check_required_features(node, ['Mood', 'Person'])
                    self.check_allowed_features(node, {
                        'Aspect': ['Imp', 'Perf'],
                        'VerbForm': ['Fin'],
                        'Mood': ['Cnd'],
                        'Person': ['1', '2', '3'],
                        'Number': ['Sing', 'Dual', 'Plur'] # optional: it is not annotated in the third person
                    })
                elif node.feats['Mood'] == 'Imp':
                    self.check_required_features(node, ['Mood', 'Person', 'Number', 'Polarity'])
                    self.check_allowed_features(node, {
                        'Aspect': ['Imp', 'Perf'],
                        'VerbForm': ['Fin'],
                        'Mood': ['Imp'],
                        'Person': ['1', '2', '3'], # 3rd person imperative occasionally occurs in old Czech (but the form is identical to 2nd person)
                        'Number': ['Sing', 'Dual', 'Plur'],
                        'Polarity': ['Pos', 'Neg']
                    })
                else: # indicative
                    self.check_required_features(node, ['Mood', 'Voice', 'Tense', 'Person', 'Number', 'Polarity'])
                    self.check_allowed_features(node, {
                        'Aspect': ['Imp', 'Perf'],
                        'VerbForm': ['Fin'],
                        'Mood': ['Ind'],
                        'Tense': ['Past', 'Imp', 'Pres', 'Fut'], # only in indicative
                        'Voice': ['Act'],
                        'Person': ['1', '2', '3'],
                        'Number': ['Sing', 'Dual', 'Plur'],
                        'Polarity': ['Pos', 'Neg'],
                        'Variant': ['Short', 'Long'] # distinguishes sigmatic (Long) and asigmatic (Short) aorist
                    })
            elif node.feats['VerbForm'] == 'Part': # only l-participle; the others are ADJ, not VERB
                if node.feats['Gender'] == 'Masc':
                    self.check_required_features(node, ['Tense', 'Gender', 'Animacy', 'Number', 'Voice', 'Polarity'])
                    self.check_allowed_features(node, {
                        'Aspect': ['Imp', 'Perf'],
                        'VerbForm': ['Part'],
                        'Tense': ['Past'],
                        'Voice': ['Act'], # passive participle is ADJ, so we will not encounter it under VERB
                        'Number': ['Sing', 'Dual', 'Plur'],
                        'Gender': ['Masc'],
                        'Animacy': ['Anim', 'Inan'],
                        'Polarity': ['Pos', 'Neg']
                    })
                else:
                    self.check_required_features(node, ['Tense', 'Gender', 'Number', 'Voice', 'Polarity'])
                    self.check_allowed_features(node, {
                        'Aspect': ['Imp', 'Perf'],
                        'VerbForm': ['Part'],
                        'Tense': ['Past'],
                        'Voice': ['Act'], # passive participle is ADJ, so we will not encounter it under VERB
                        'Number': ['Sing', 'Dual', 'Plur'],
                        'Gender': ['Fem', 'Neut'],
                        'Polarity': ['Pos', 'Neg']
                    })
            else: # converb
                self.check_required_features(node, ['Tense', 'Number', 'Voice', 'Polarity'])
                self.check_allowed_features(node, {
                    'Aspect': ['Imp', 'Perf'],
                    'VerbForm': ['Conv'],
                    'Tense': ['Past', 'Pres'],
                    'Voice': ['Act'],
                    'Number': ['Sing', 'Dual', 'Plur'],
                    'Gender': ['Masc', 'Fem', 'Neut'], # annotated only in singular, and no animacy
                    'Polarity': ['Pos', 'Neg']
                })
        # ADVERBS ##############################################################
        elif node.upos == 'ADV':
            if node.feats['PronType'] != '':
                # Pronominal adverbs are neither compared nor negated.
                self.check_allowed_features(node, {
                    'PronType': ['Dem', 'Int,Rel', 'Ind', 'Neg', 'Tot']
                })
            elif node.feats['Degree'] != '':
                # Adverbs that are compared can also be negated.
                self.check_required_features(node, ['Degree', 'Polarity'])
                self.check_allowed_features(node, {
                    'Degree': ['Pos', 'Cmp', 'Sup'],
                    'Polarity': ['Pos', 'Neg']
                })
            else:
                # The remaining adverbs are neither pronominal, nor compared or
                # negated.
                self.check_allowed_features(node, {})
        # ADPOSITIONS ##########################################################
        elif node.upos == 'ADP':
            self.check_required_features(node, ['AdpType', 'Case'])
            self.check_allowed_features(node, {
                'AdpType': ['Prep', 'Voc'],
                'Case': ['Gen', 'Dat', 'Acc', 'Loc', 'Ins']
            })
        # THE REST: NO FEATURES ################################################
        else:
            self.check_allowed_features(node, {})

    def check_adjective_like(self, node, r0, a0):
        """
        Long form of adjectives, pronouns and determiners mostly share declension
        paradigms and thus the sets of features that are expected. Whether the
        actual feature sets are the same depends on the tagging convention (PDT
        vs. ČNK): in PDT, adjectives are fully disambiguated while pronouns are
        not; in ČNK, both adjectives and pronouns (incl. determiners) are fully
        disambiguated. This method defines the core inflectional features while
        any extras (such as PronType for pronouns) have to be provided by the
        caller in parameters r0 (list) and a0 (dict).
        """
        required_features = []
        allowed_featurs = {}
        full_set = node.upos == 'ADJ' or not self.pdt20
        if full_set:
            # Even in the full set, animacy is only distinguished for the
            # masculine gender.
            if node.feats['Gender'] == 'Masc':
                required_features = ['Gender', 'Animacy', 'Number', 'Case']
                allowed_features = {
                    'Gender': ['Masc'],
                    'Animacy': ['Anim', 'Inan'],
                    'Number': ['Sing', 'Dual', 'Plur'],
                    'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins']
                }
            else:
                required_features = ['Gender', 'Number', 'Case']
                allowed_features = {
                    'Gender': ['Fem', 'Neut'],
                    'Number': ['Sing', 'Dual', 'Plur'],
                    'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins']
                }
        else:
            # Gender is annotated in all cases in singular (ten, ta, to)
            # but only in nominative, accusative, and vocative in plural
            # (Nom/Voc ti, ty, ta; Acc ty, ta). Animacy is distinguished
            # in plural if gender is distinguished and it is masculine; in
            # singular it is distinguished only in accusative (toho, ten).
            # Other cases in plural are gender-less (těch, těm, těmi).
            # Note that this is not consistent with adjectives, where we
            # disambiguate gender in all cases in plural.
            if node.feats['Number'] == 'Sing':
                if node.feats['Gender'] == 'Masc' and node.feats['Case'] == 'Acc':
                    required_features = ['Gender', 'Animacy', 'Number', 'Case']
                    allowed_features = {
                        'Gender': ['Masc'],
                        'Animacy': ['Anim', 'Inan'],
                        'Number': ['Sing'],
                        'Case': ['Acc']
                    }
                else:
                    required_features = ['Gender', 'Number', 'Case']
                    allowed_features = {
                        'Gender': ['Masc', 'Masc,Neut', 'Fem', 'Fem,Neut', 'Neut'], # non-nominative forms of Masc and Neut are merged; Fem,Neut is e.g. 'vaše' in singular
                        'Number': ['Sing'],
                        'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins']
                    }
            elif re.match(r'^(Nom|Acc|Voc)$', node.feats['Case']):
                required_features = ['Gender', 'Number', 'Case']
                allowed_features = {
                    'Gender': ['Masc', 'Fem', 'Neut'],
                    'Animacy': ['Anim', 'Inan'],
                    'Number': ['Dual', 'Plur'],
                    'Case': ['Nom', 'Acc', 'Voc']
                }
            else:
                required_features = ['Number', 'Case']
                allowed_features = {
                    'Number': ['Dual', 'Plur'],
                    'Case': ['Gen', 'Dat', 'Loc', 'Ins']
                }
        required_features = r0 + required_features
        a0.update(allowed_features)
        allowed_features = a0
        self.check_required_features(node, required_features)
        self.check_allowed_features(node, allowed_features)
