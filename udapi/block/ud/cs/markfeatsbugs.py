"""
Block to identify missing or ill-valued features in Czech. Any bugs that it
finds will be saved in the MISC column as a Bug attribute, which can be later
used in filters and highlighted in text output.

Usage: cat *.conllu | udapy -HAMX layout=compact ud.cs.MarkFeatsBugs > bugs.html
Windows: python udapy read.Conllu files="a.conllu,b.conllu" merge=1 ud.cs.MarkFeatsBugs write.TextModeTreesHtml files="bugs.html" marked_only=1 layout=compact attributes=form,lemma,upos,xpos,feats,deprel,misc
"""
import udapi.block.ud.markfeatsbugs
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
            self.check_required_features(node, ['Gender', 'Number', 'Case'])
            if node.feats['VerbForm'] == 'Vnoun':
                # verbal nouns: bytí, dělání, ...
                self.check_allowed_features(node, {
                    'VerbForm': ['Vnoun'],
                    'Gender': ['Neut'],
                    'Number': ['Sing', 'Dual', 'Plur'],
                    'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                    'Foreign': ['Yes']
                })
            elif node.feats['Gender'] == 'Masc':
                self.check_required_features(node, ['Animacy'])
                self.check_allowed_features(node, {
                    'Gender': ['Masc', 'Fem', 'Neut'],
                    'Animacy': ['Anim', 'Inan'],
                    'Number': ['Sing', 'Dual', 'Plur'],
                    'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                    'Foreign': ['Yes']})
            else:
                self.check_allowed_features(node, {
                    'Gender': ['Masc', 'Fem', 'Neut'],
                    'Number': ['Sing', 'Dual', 'Plur'],
                    'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                    'Foreign': ['Yes']})
        # PROPER NOUNS #########################################################
        elif node.upos == 'PROPN':
            self.check_required_features(node, ['Gender', 'Number', 'Case'])
            if node.feats['Gender'] == 'Masc':
                self.check_required_features(node, ['Animacy'])
                self.check_allowed_features(node, {
                    'Gender': ['Masc', 'Fem', 'Neut'],
                    'Animacy': ['Anim', 'Inan'],
                    'Number': ['Sing', 'Dual', 'Plur'],
                    'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                    'NameType': ['Giv', 'Sur', 'Geo', 'Nat'],
                    'Foreign': ['Yes']})
            else:
                self.check_allowed_features(node, {
                    'Gender': ['Masc', 'Fem', 'Neut'],
                    'Number': ['Sing', 'Dual', 'Plur'],
                    'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                    'NameType': ['Giv', 'Sur', 'Geo', 'Nat'],
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
                        'NameType': ['Giv', 'Sur', 'Nat'], # for possessive adjectives derived from personal names
                        'Emph': ['Yes'],
                        'Foreign': ['Yes']})
                else:
                    self.check_required_features(node, ['Poss', 'Gender[psor]', 'Gender', 'Number', 'Case'])
                    self.check_allowed_features(node, {
                        'Poss': ['Yes'],
                        'Gender[psor]': ['Masc', 'Fem'],
                        'Gender': ['Masc', 'Fem', 'Neut'],
                        'Number': ['Sing', 'Dual', 'Plur'],
                        'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                        'NameType': ['Giv', 'Sur', 'Nat'], # for possessive adjectives derived from personal names
                        'Emph': ['Yes'],
                        'Foreign': ['Yes']})
            elif node.feats['NumType'] == 'Ord' or node.feats['NumType'] == 'Mult': # ordinal numerals are a subtype of adjectives; same for some multiplicative numerals (dvojí, trojí)
                if node.feats['Gender'] == 'Masc':
                    self.check_required_features(node, ['NumType', 'Gender', 'Animacy', 'Number', 'Case'])
                    self.check_allowed_features(node, {
                        'NumType': ['Ord', 'Mult'],
                        'Gender': ['Masc', 'Fem', 'Neut'],
                        'Animacy': ['Anim', 'Inan'],
                        'Number': ['Sing', 'Dual', 'Plur'],
                        'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                        'Emph': ['Yes'],
                        'Foreign': ['Yes']})
                else:
                    self.check_required_features(node, ['NumType', 'Gender', 'Number', 'Case'])
                    self.check_allowed_features(node, {
                        'NumType': ['Ord', 'Mult'],
                        'Gender': ['Masc', 'Fem', 'Neut'],
                        'Number': ['Sing', 'Dual', 'Plur'],
                        'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                        'Emph': ['Yes'],
                        'Foreign': ['Yes']})
            elif node.feats['VerbForm'] == 'Part': # participles (except l-participles) are a subtype of adjectives
                self.check_required_features(node, ['VerbForm', 'Voice'])
                if node.feats['Voice'] == 'Act': # active participles have tense, passives don't but they have degree
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
                            'Emph': ['Yes'],
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
                            'Emph': ['Yes'],
                            'Foreign': ['Yes']})
                else:
                    if node.feats['Gender'] == 'Masc':
                        self.check_required_features(node, ['VerbForm', 'Aspect', 'Voice', 'Gender', 'Animacy', 'Number', 'Case', 'Polarity', 'Degree'])
                        self.check_allowed_features(node, {
                            'VerbForm': ['Part'],
                            'Aspect': ['Imp', 'Perf'],
                            'Voice': ['Pass'],
                            'Gender': ['Masc', 'Fem', 'Neut'],
                            'Animacy': ['Anim', 'Inan'],
                            'Number': ['Sing', 'Dual', 'Plur'],
                            'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                            'Polarity': ['Pos', 'Neg'],
                            'Degree': ['Pos', 'Cmp', 'Sup'],
                            'Variant': ['Short'],
                            'Emph': ['Yes'],
                            'Foreign': ['Yes']})
                    else:
                        self.check_required_features(node, ['VerbForm', 'Aspect', 'Voice', 'Gender', 'Number', 'Case', 'Polarity', 'Degree'])
                        self.check_allowed_features(node, {
                            'VerbForm': ['Part'],
                            'Aspect': ['Imp', 'Perf'],
                            'Voice': ['Pass'],
                            'Gender': ['Masc', 'Fem', 'Neut'],
                            'Number': ['Sing', 'Dual', 'Plur'],
                            'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                            'Polarity': ['Pos', 'Neg'],
                            'Degree': ['Pos', 'Cmp', 'Sup'],
                            'Variant': ['Short'],
                            'Emph': ['Yes'],
                            'Foreign': ['Yes']})
            else: # regular adjectives, including short forms
                if node.feats['Gender'] == 'Masc':
                    self.check_required_features(node, ['Gender', 'Animacy', 'Number', 'Case', 'Degree', 'Polarity'])
                    self.check_allowed_features(node, {
                        'Gender': ['Masc', 'Fem', 'Neut'],
                        'Animacy': ['Anim', 'Inan'],
                        'Number': ['Sing', 'Dual', 'Plur'],
                        'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                        'Degree': ['Pos', 'Cmp', 'Sup'],
                        'Polarity': ['Pos', 'Neg'],
                        'Variant': ['Short'],
                        'Emph': ['Yes'],
                        'Foreign': ['Yes']})
                else:
                    self.check_required_features(node, ['Gender', 'Number', 'Case', 'Degree', 'Polarity'])
                    self.check_allowed_features(node, {
                        'Gender': ['Masc', 'Fem', 'Neut'],
                        'Number': ['Sing', 'Dual', 'Plur'],
                        'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                        'Degree': ['Pos', 'Cmp', 'Sup'],
                        'Polarity': ['Pos', 'Neg'],
                        'Variant': ['Short'],
                        'Emph': ['Yes'],
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
                        elif re.match(r"^(ho|mu)$", node.form.lower()):
                            # The short (clitic) forms do not have PrepCase in Modern Czech.
                            # Old Czech has also 'jmu' (besides 'jemu' and 'mu') and 'jho'
                            # (besides 'jeho' and 'ho'); it should not have Variant=Short
                            # and it should have PrepCase=Npr (the next block).
                            self.check_adjective_like(node, ['PronType', 'Person', 'Variant'], {
                                'PronType': ['Prs'],
                                'Person': ['3'],
                                'Variant': ['Short']
                            })
                        else: # jeho, něho, jemu, němu, jej, něj, něm, jím, ním, jí, ní, ji, ni, je, ně
                            # Mostly only two gender groups and no animacy:
                            # Masc,Neut ... jeho, jho, jemu, jmu, jej, něm, jím
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
            elif re.search(r'k[dt][oe]', node.lemma): # kdo (kto), kdož, někdo, nikdo
                # There is no Number. Někdo and nikdo behave like singular;
                # kdo is by default singular as well but it also occurs as subject
                # of plural verbs ("ti, kdo nepřišli včas, byli vyloučeni").
                # In Old Czech, "nikde" is a variant of the pronoun "nikdo" (nobody)
                # (while in New Czech, "nikde" (nowhere) is a pronominal adverb only).
                # Old Czech data disambiguate Int from Rel (Int is used only in direct questions with; indirect questions like "Ptal ses, kdo to je?" use Rel.)
                # New Czech data, in particular PDT, use Int,Rel regardless of context.
                self.check_required_features(node, ['PronType', 'Gender', 'Animacy', 'Case'])
                self.check_allowed_features(node, {
                    'PronType': ['Int,Rel', 'Int', 'Rel', 'Ind', 'Neg'],
                    'Gender': ['Masc'],
                    'Animacy': ['Anim'],
                    'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Loc', 'Ins']
                })
            elif re.match(r'^(co|což|což?koliv?|něco|lečco|lecco|nic|nicož)$', node.lemma):
                # Although these pronouns behave by default as neuter singular,
                # no Gender and Number is annotated. However, quite unusually,
                # there is Animacy=Inan without Gender.
                ###!!! This should probably be fixed in all Czech treebanks and
                ###!!! in Interset. The pronoun should get Gender=Neut and no
                ###!!! animacy. For now, let's at least make animacy an optional
                ###!!! feature (I see that we already do not fill it in the Old
                ###!!! Czech data).
                # Old Czech data disambiguate Int from Rel (Int is used only in direct questions with; indirect questions like "Ptal ses, co to je?" use Rel.)
                # New Czech data, in particular PDT, use Int,Rel regardless of context.
                self.check_required_features(node, ['PronType', 'Case'])
                self.check_allowed_features(node, {
                    'PronType': ['Int,Rel', 'Int', 'Rel', 'Ind', 'Neg'],
                    'Animacy': ['Inan'],
                    'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Loc', 'Ins']
                })
            elif node.lemma == 'ješto':
                # Unlike 'jenžto', this relative pronoun does not inflect, it
                # always occurs in a nominative position, but the context can
                # be any gender and number.
                # Update from the Hičkok project: 'ješto' is lemmatized to
                # 'jenžto' (see below), meaning that this branch should not be
                # needed for the new data.
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
                # Update from the Hičkok project: In Old Czech, both 'jenž' and
                # 'jenžto' (or its variant 'ješto') can be used uninflected,
                # accompanied by a resumptive pronoun which provides the inflection.
                # In this case, the Hičkok data will not annotate Gender, Animacy,
                # Number and Case of the relative pronoun. Therefore, we require
                # the full set of features if any of them is present; otherwise,
                # we only expect PronType and PrepCase.
                if node.feats['Gender'] != '' or node.feats['Animacy'] != '' or node.feats['Number'] != '' or node.feats['Case'] != '':
                    self.check_adjective_like(node, ['PronType', 'PrepCase'], {
                        'PronType': ['Rel'],
                        'PrepCase': ['Npr', 'Pre']
                    })
                else:
                    self.check_required_features(node, ['PronType', 'PrepCase'])
                    self.check_allowed_features(node, {
                        'PronType': ['Rel'],
                        'PrepCase': ['Npr']
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
                        'Animacy': ['Anim', 'Inan'],
                        'Number': ['Sing', 'Dual', 'Plur'],
                        'Case': ['Nom']
                    })
        # DETERMINERS ##########################################################
        elif node.upos == 'DET':
            # Possessive determiners 'jeho' and 'jejich' (formerly 'jich') do not inflect, i.e., no Gender, Number, Case.
            # Note that the possessive determiner 'její' (formerly 'jejie') does inflect, although it also has the lemma 'jeho'.
            if re.match(r'^(je?ho|jejich|j[ií]ch)$', node.form.lower()):
                self.check_required_features(node, ['PronType', 'Poss', 'Person', 'Number[psor]'])
                self.check_allowed_features(node, {
                    'PronType': ['Prs'],
                    'Poss': ['Yes'],
                    'Person': ['3'],
                    'Number[psor]': ['Sing', 'Dual', 'Plur'],
                    'Gender[psor]': ['Masc', 'Neut', 'Masc,Neut'],
                    'Gender': ['Masc', 'Fem', 'Neut'], # uninflected in modern Czech, but old Czech annotations sometime indicate the modified gender by context
                    'Animacy': ['Anim', 'Inan'], # uninflected in modern Czech, but old Czech annotations sometime indicate the modified gender by context
                    'Number': ['Sing', 'Dual', 'Plur'], # uninflected in modern Czech, but old Czech annotations sometime indicate the modified number by context
                    'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'] # uninflected in modern Czech, but old Czech annotations sometime indicate the case by context
                    # PrepCase is not allowed when it is a possessive determiner because no n-form can be used (jeho dům VS. na jeho dům).
                    # Compare with genitive/accusative of the pronoun "on", there the form changes after preposition and PrepCase must be annotated
                    # (jeho se bojím VS. bez něho se neobejdu).
                })
            # Relative possessive determiners 'jehož' and 'jejichž' behave similarly
            # to the personal possessive determiners but they do not have Person.
            elif re.match(r'^(jeho|jejich|j[ií]ch)ž(e|to)?$', node.form.lower()):
                self.check_required_features(node, ['PronType', 'Poss', 'Number[psor]'])
                self.check_allowed_features(node, {
                    'PronType': ['Rel'],
                    'Poss': ['Yes'],
                    'Number[psor]': ['Sing', 'Dual', 'Plur'],
                    'Gender[psor]': ['Masc', 'Neut', 'Masc,Neut'],
                    'Gender': ['Masc', 'Fem', 'Neut'], # uninflected in modern Czech, but old Czech annotations sometime indicate the modified gender by context
                    'Animacy': ['Anim', 'Inan'], # uninflected in modern Czech, but old Czech annotations sometime indicate the modified gender by context
                    'Number': ['Sing', 'Dual', 'Plur'], # uninflected in modern Czech, but old Czech annotations sometime indicate the modified number by context
                    'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'] # uninflected in modern Czech, but old Czech annotations sometime indicate the case by context
                    # PrepCase is not allowed when it is a possessive determiner (muž, jehož manželka zahynula při nehodě) because no n-form can be used
                    # (after preposition: muž, na jehož manželku jste si stěžoval). Compare with genitive/accusative of the relative pronoun "jenž",
                    # there the form changes after preposition and PrepCase must be annotated (muž, jehož se bojím VS. muž, bez něhož se neobejdeme).
                })
            # Feminine personal possessive determiner.
            elif re.match(r'^(její|jejie|jejího|jejieho|jejímu|jejiemu|jejím|jejiem|jejiej|jejíma|jejiema|jejích|jejiech|jejími|jejiemi)$', node.form.lower()):
                # The feminine possessive 'její' slightly inflects, unlike 'jeho' and 'jejich'.
                # Congruent gender:
                # - in PDT, only in singular; masculine and neuter are merged even in nominative
                # - in Old Czech data, gender is disambiguated by context (no merging), even in dual and plural
                # Case:
                # - in PDT, not distinguished in feminine singular (její bota, její boty, její botě, její botu...)
                # - in Old Czech data, distinguished always (and needed at least for 'jejiej')
                if self.pdt20:
                    if node.feats['Number'] == 'Sing':
                        self.check_required_features(node, ['PronType', 'Poss', 'Person', 'Number[psor]', 'Gender[psor]', 'Gender', 'Number', 'Case'])
                        self.check_allowed_features(node, {
                            'PronType': ['Prs'],
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
                            'PronType': ['Prs'],
                            'Poss': ['Yes'],
                            'Person': ['3'],
                            'Number[psor]': ['Sing'],
                            'Gender[psor]': ['Fem'],
                            'Number': ['Dual', 'Plur'],
                            'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins']
                        })
                else:
                    self.check_required_features(node, ['PronType', 'Poss', 'Person', 'Number[psor]', 'Gender[psor]', 'Gender', 'Number', 'Case'])
                    self.check_allowed_features(node, {
                        'PronType': ['Prs'],
                        'Poss': ['Yes'],
                        'Person': ['3'],
                        'Number[psor]': ['Sing'],
                        'Gender[psor]': ['Fem'],
                        'Gender': ['Masc', 'Neut', 'Fem'],
                        'Animacy': ['Anim', 'Inan'], # only for Gender=Masc
                        'Number': ['Sing', 'Dual', 'Plur'],
                        'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins']
                    })
            # Feminine relative possessive determiner.
            elif re.match(r'^(její|jejie|jejího|jejieho|jejímu|jejiemu|jejím|jejiem|jejiej|jejíma|jejiema|jejích|jejiech|jejími|jejiemi)(ž(e|to)?)$', node.form.lower()):
                # The feminine possessive 'jejíž' slightly inflects, unlike 'jehož' and 'jejichž'.
                # Congruent gender:
                # - in PDT, only in singular; masculine and neuter are merged even in nominative
                # - in Old Czech data, gender is disambiguated by context (no merging), even in dual and plural
                # Case:
                # - in PDT, not distinguished in feminine singular (jejíž bota, jejíž boty, jejíž botě, jejíž botu...)
                # - in Old Czech data, distinguished always (and needed at least for 'jejiejž')
                if self.pdt20:
                    if node.feats['Number'] == 'Sing':
                        self.check_required_features(node, ['PronType', 'Poss', 'Number[psor]', 'Gender[psor]', 'Gender', 'Number', 'Case'])
                        self.check_allowed_features(node, {
                            'PronType': ['Rel'],
                            'Poss': ['Yes'],
                            'Number[psor]': ['Sing'],
                            'Gender[psor]': ['Fem'],
                            'Gender': ['Masc,Neut', 'Fem'],
                            'Number': ['Sing'],
                            'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins']
                        })
                    else:
                        self.check_required_features(node, ['PronType', 'Poss', 'Number[psor]', 'Gender[psor]', 'Number', 'Case'])
                        self.check_allowed_features(node, {
                            'PronType': ['Rel'],
                            'Poss': ['Yes'],
                            'Number[psor]': ['Sing'],
                            'Gender[psor]': ['Fem'],
                            'Number': ['Dual', 'Plur'],
                            'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins']
                        })
                else:
                    self.check_required_features(node, ['PronType', 'Poss', 'Number[psor]', 'Gender[psor]', 'Gender', 'Number', 'Case'])
                    self.check_allowed_features(node, {
                        'PronType': ['Rel'],
                        'Poss': ['Yes'],
                        'Number[psor]': ['Sing'],
                        'Gender[psor]': ['Fem'],
                        'Gender': ['Masc', 'Neut', 'Fem'],
                        'Animacy': ['Anim', 'Inan'], # only for Gender=Masc
                        'Number': ['Sing', 'Dual', 'Plur'],
                        'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins']
                    })
            elif re.match(r'^(můj|tvůj|svůj)$', node.lemma):
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
            elif re.match(r'^(ně|lec|ni)?číž?(koliv?)?$', node.lemma):
                self.check_adjective_like(node, ['PronType', 'Poss'], {
                    'PronType': ['Int', 'Rel', 'Ind', 'Neg'],
                    'Poss': ['Yes']
                })
            elif re.match(r'^(sám|samý)$', node.lemma):
                # The above condition looks at both lemma options, although only one lemma is assumed.
                # However, in New Czech data the one lemma is "samý" while in Old Czech data it is "sám".
                # Unlike other determiners, it allows Variant=Short: sám, sama, samu, samo, sami, samy.
                self.check_adjective_like(node, ['PronType'], {'PronType': ['Emp'], 'Variant': ['Short']})
            elif node.lemma == 'žádný':
                # In Old Czech, this determiner also allows Variant=Short: žáden, žádna, žádnu, žádno, žádni, žádny.
                self.check_adjective_like(node, ['PronType'], {'PronType': ['Neg'], 'Variant': ['Short']})
            elif node.feats['NumType'] == 'Card': # pronominal quantifiers 'mnoho', 'málo', 'několik' etc.
                if node.lemma == 'nejeden':
                    self.check_adjective_like(node, ['PronType', 'NumType'], {'PronType': ['Ind'], 'NumType': ['Card']})
                else:
                    # Lemmas 'hodně' and 'málo' have Degree even if used as quantifiers and not adverbs:
                    # hodně, více, nejvíce; málo, méně, nejméně
                    # Lemmas 'mnoho' and 'málo' can be negated (nemnoho, nemálo).
                    self.check_required_features(node, ['PronType', 'NumType', 'Case'])
                    self.check_allowed_features(node, {
                        'PronType': ['Ind', 'Int', 'Rel', 'Dem'],
                        'NumType': ['Card'],
                        'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                        'Degree': ['Pos', 'Cmp', 'Sup'],
                        'Polarity': ['Pos', 'Neg']
                    })
            else:
                # Old Czech data disambiguate Int from Rel (Int is used only in direct questions with; indirect questions like "Ptal ses, kde to je?" use Rel.)
                # New Czech data, in particular PDT, use Int,Rel regardless of context.
                self.check_adjective_like(node, ['PronType'], {'PronType': ['Dem', 'Int,Rel', 'Int', 'Rel', 'Ind', 'Neg', 'Tot']})
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
                # 'půl' has no Number and Case, although it behaves syntactically similarly to 'pět' (but genitive is still 'půl', not '*půli').
                # 'sto', 'tisíc', 'milión', 'miliarda' etc. have Gender (+ possibly Animacy) and Number (depending on their form).
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
                            'PronType': ['Tot'], # for 'oba'
                            'NumForm': ['Word'],
                            'Gender': ['Masc', 'Masc,Neut', 'Fem', 'Fem,Neut', 'Neut'], # similarly to determiners, genders are merged in some slots of the paradigm
                            'Number': ['Dual', 'Plur'],
                            'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins']
                        })
                    else:
                        self.check_allowed_features(node, {
                            'NumType': ['Card'],
                            'PronType': ['Tot'], # for 'oba'
                            'NumForm': ['Word'],
                            'Gender': ['Masc', 'Fem', 'Neut'],
                            'Animacy': ['Anim', 'Inan'],
                            'Number': ['Dual', 'Plur'],
                            'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins']
                        })
                elif node.lemma == 'půl':
                    self.check_required_features(node, ['NumType', 'NumForm'])
                    self.check_allowed_features(node, {
                        'NumType': ['Card'],
                        'NumForm': ['Word']
                    })
                elif re.match(r'^(sto|tisíc|.+ili[oó]n|.+iliarda)$', node.lemma):
                    self.check_required_features(node, ['NumType', 'NumForm', 'Number', 'Case'])
                    self.check_allowed_features(node, {
                        'NumType': ['Card', 'Sets'],
                        'NumForm': ['Word'],
                        'Gender': ['Masc', 'Fem', 'Neut'],
                        'Animacy': ['Anim', 'Inan'],
                        'Number': ['Sing', 'Dual', 'Plur'],
                        'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins']
                    })
                else:
                    # In PDT, cardinal numerals higher than four in nominative/accusative/vocative
                    # have Number=Sing instead of Plur! It may be motivated by the default
                    # agreement they trigger on verbs (but they don't have Gender=Neut).
                    # It does not make much sense but we must allow Sing before a better
                    # approach is defined and implemented in the data.
                    # On the other hand, we may want to allow Dual for "stě".
                    self.check_required_features(node, ['NumType', 'NumForm', 'Number', 'Case'])
                    self.check_allowed_features(node, {
                        'NumType': ['Card', 'Sets'],
                        'NumForm': ['Word'],
                        'Number': ['Sing', 'Dual', 'Plur'],
                        'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins']
                    })
        # VERBS AND AUXILIARIES ################################################
        elif node.upos in ['VERB', 'AUX']:
            # There are only three lemmas recognized as AUX in Czech. This is not
            # about features and it would be caught by the UD validator, but it
            # is error in morphology, so let's report it here as well.
            if node.upos == 'AUX' and node.lemma not in ['být', 'bývat', 'bývávat']:
                self.bug(node, 'NonAuxLemma')
            # All Czech verbs (and some adjectives and nouns) must have VerbForm.
            # Almost all verbs have lexical Aspect but we cannot require it
            # because there are a few biaspectual verbs (e.g. 'analyzovat') that
            # do not have the feature.
            self.check_required_features(node, ['VerbForm'])
            if node.feats['VerbForm'] in ['Inf', 'Sup']:
                # There is no voice. For some reason, PDT does not annotate that
                # the infinitive form is active (while a passive infinitive is
                # a combination of the infinitive with a passive participle).
                self.check_required_features(node, ['Polarity'])
                self.check_allowed_features(node, {
                    'Aspect': ['Imp', 'Perf'],
                    'VerbForm': ['Inf', 'Sup'],
                    'Polarity': ['Pos', 'Neg']
                })
            elif node.feats['VerbForm'] == 'Fin':
                # Voice is optional. For some reason it is not annotated with
                # imperatives (although passive imperatives are a combination
                # of the active imperative and a passive participle). It is
                # also not annotated at the conditional auxiliary 'bych', 'bys', 'by', 'bychom', 'byste'.
                # Conditional "by" has no person and number (it is typically
                # 3rd person but it could be other persons, too, as in "ty by
                # ses bál").
                if node.feats['Mood'] == 'Cnd':
                    if node.form.lower() == 'by':
                        self.check_required_features(node, ['Mood'])
                        self.check_allowed_features(node, {
                            'Aspect': ['Imp'],
                            'VerbForm': ['Fin'],
                            'Mood': ['Cnd']
                        })
                    else:
                        self.check_required_features(node, ['Mood', 'Person', 'Number'])
                        self.check_allowed_features(node, {
                            'Aspect': ['Imp'],
                            'VerbForm': ['Fin'],
                            'Mood': ['Cnd'],
                            'Person': ['1', '2'],
                            'Number': ['Sing', 'Dual', 'Plur']
                        })
                elif node.feats['Mood'] == 'Imp':
                    self.check_required_features(node, ['Mood', 'Person', 'Number', 'Polarity'])
                    self.check_allowed_features(node, {
                        'Aspect': ['Imp', 'Perf'],
                        'VerbForm': ['Fin'],
                        'Mood': ['Imp'],
                        'Voice': ['Act'], # optional in Old Czech data, not used with imperatives in Modern Czech data (at least not yet)
                        'Person': ['1', '2', '3'], # 3rd person imperative occasionally occurs in old Czech (but the form is identical to 2nd person)
                        'Number': ['Sing', 'Dual', 'Plur'],
                        'Polarity': ['Pos', 'Neg'],
                        'Emph': ['Yes']
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
                # Old Czech data annotate converb gender by context rather than form
                # (because the form was different than in Modern Czech) and for
                # masculines they also include animacy. In Modern Czech animacy is
                # currently not annotated and Masc,Neut gender is merged.
                if node.feats['Number'] == 'Sing':
                    if node.feats['Gender'] == 'Masc':
                        self.check_required_features(node, ['Tense', 'Gender', 'Animacy', 'Number', 'Voice', 'Polarity'])
                        self.check_allowed_features(node, {
                            'Aspect': ['Imp', 'Perf'],
                            'VerbForm': ['Conv'],
                            'Tense': ['Past', 'Pres'],
                            'Voice': ['Act'], # passive participle is ADJ, so we will not encounter it under VERB
                            'Number': ['Sing'],
                            'Gender': ['Masc'],
                            'Animacy': ['Anim', 'Inan'],
                            'Polarity': ['Pos', 'Neg']
                        })
                    else:
                        self.check_required_features(node, ['Tense', 'Gender', 'Number', 'Voice', 'Polarity'])
                        self.check_allowed_features(node, {
                            'Aspect': ['Imp', 'Perf'],
                            'VerbForm': ['Conv'],
                            'Tense': ['Past', 'Pres'],
                            'Voice': ['Act'], # passive participle is ADJ, so we will not encounter it under VERB
                            'Number': ['Sing'],
                            'Gender': ['Fem', 'Neut'],
                            'Polarity': ['Pos', 'Neg']
                        })
                else:
                    self.check_required_features(node, ['Tense', 'Number', 'Voice', 'Polarity'])
                    self.check_allowed_features(node, {
                        'Aspect': ['Imp', 'Perf'],
                        'VerbForm': ['Conv'],
                        'Tense': ['Past', 'Pres'],
                        'Voice': ['Act'],
                        'Number': ['Dual', 'Plur'],
                        'Polarity': ['Pos', 'Neg']
                    })
        # ADVERBS ##############################################################
        elif node.upos == 'ADV':
            if node.feats['NumType'] != '':
                # Adverbial multiplicative numerals (jednou, dvakrát, třikrát)
                # belong here. They have also pronominal counterparts (kolikrát,
                # tolikrát, několikrát). There are also adverbial ordinal numerals
                # (zaprvé, poprvé, zadruhé, podruhé).
                # Old Czech data disambiguate Int from Rel (Int is used only in direct questions with question mark; indirect questions like "Ptal ses, kde to je?" use Rel.)
                # New Czech data, in particular PDT, use Int,Rel regardless of context.
                self.check_allowed_features(node, {
                    'NumType': ['Mult', 'Ord'],
                    'PronType': ['Dem', 'Int', 'Rel', 'Int,Rel', 'Ind']
                })
            elif self.pdt20:
                if node.feats['PronType'] != '':
                    # Pronominal adverbs in PDT are neither compared nor negated.
                    # New Czech data, in particular PDT, use Int,Rel regardless of context.
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
            else:
                if node.feats['PronType'] == 'Tot':
                    # Total adverbs in Old Czech can be negated: vždy, nevždy.
                    # Then for consistence with other adverbs, we also require
                    # Degree, although it will be always Pos.
                    self.check_required_features(node, ['Degree', 'Polarity'])
                    self.check_allowed_features(node, {
                        'PronType': ['Tot'],
                        'Degree': ['Pos'],
                        'Polarity': ['Pos', 'Neg']
                    })
                elif node.feats['PronType'] != '':
                    # Other pronominal adverbs are neither compared nor negated.
                    # Old Czech data disambiguate Int from Rel (Int is used only in direct questions with question mark; indirect questions like "Ptal ses, kde to je?" use Rel.)
                    self.check_allowed_features(node, {
                        'PronType': ['Dem', 'Int', 'Rel', 'Ind', 'Neg']
                    })
                else:
                    # All other adverbs should have both Degree and Polarity,
                    # although for some of them the values will always be Pos.
                    self.check_required_features(node, ['Degree', 'Polarity'])
                    self.check_allowed_features(node, {
                        'Degree': ['Pos', 'Cmp', 'Sup'],
                        'Polarity': ['Pos', 'Neg'],
                        'Emph': ['Yes']
                    })
        # ADPOSITIONS ##########################################################
        elif node.upos == 'ADP':
            self.check_required_features(node, ['AdpType', 'Case'])
            self.check_allowed_features(node, {
                'AdpType': ['Prep', 'Voc'],
                'Case': ['Gen', 'Dat', 'Acc', 'Loc', 'Ins'],
                'Abbr': ['Yes']
            })
        # SUBORDINATING CONJUNCTIONS ###########################################
        elif node.upos == 'SCONJ':
            self.check_allowed_features(node, {
                'Emph': ['Yes']
            })
        # COORDINATING CONJUNCTIONS ############################################
        elif node.upos == 'CCONJ':
            self.check_allowed_features(node, {
                'Emph': ['Yes']
            })
        # PARTICLES ############################################################
        elif node.upos == 'PART':
            # "t." = "totiž"
            self.check_allowed_features(node, {
                'Abbr': ['Yes']
            })
        # THE REST: NO FEATURES ################################################
        # (OR UNDEFINED UPOS) ##################################################
        else:
            if not node.upos in ['INTJ', 'PUNCT', 'SYM', 'X']:
                bugmsg = 'UnknownUpos'
                if node.upos:
                    bugmsg += node.upos
                self.bug(node, bugmsg)
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
        allowed_features = {}
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
