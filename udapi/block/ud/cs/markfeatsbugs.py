"""
Block to identify missing or ill-valued features in Czech. Any bugs that it
finds will be saved in the MISC column as a Bug attribute, which can be later
used in filters and highlighted in text output.
"""
from udapi.core.block import Block
import logging
import re

class MarkFeatsBugs(Block):

    allowed = {
        'NOUN': {'Gender': ['Masc', 'Fem', 'Neut'],
                 'Animacy': ['Anim', 'Inan'],
                 'Number': ['Sing', 'Dual', 'Plur'],
                 'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                 'Polarity': ['Pos', 'Neg'],
                 'Foreign': ['Yes']},
        'ADJ':  {'Gender': ['Masc', 'Fem', 'Neut'],
                 'Animacy': ['Anim', 'Inan'],
                 'Number': ['Sing', 'Dual', 'Plur'],
                 'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                 'Degree': ['Pos', 'Cmp', 'Sup'],
                 'Polarity': ['Pos', 'Neg'],
                 'Variant': ['Short'],
                 'Poss': ['Yes'],
                 'Gender[psor]': ['Masc', 'Fem'],
                 'NameType': ['Giv', 'Sur'], # for possessive adjectives derived from personal names
                 'NumType': ['Ord'],
                 'VerbForm': ['Part'],
                 'Aspect': ['Imp', 'Perf'],
                 'Tense': ['Pres', 'Past'],
                 'Voice': ['Act', 'Pass'],
                 'Foreign': ['Yes']}
    }

    required = {
        'NOUN': ['Gender', 'Number', 'Case', 'Polarity'],
        'ADJ': ['Gender', 'Number', 'Case', 'Degree', 'Polarity']
    }

    def bug(self, node, bugstring):
        bugs = []
        if node.misc['Bug']:
            bugs = node.misc['Bug'].split('+')
        if not bugstring in bugs:
            bugs.append(bugstring)
        node.misc['Bug'] = '+'.join(bugs)

    def check_allowed_features(self, node, allowed):
        """
        We need a dictionary indexed by feature names that are allowed; for each
        feature name, there is a list of allowed values.
        """
        # Check for features that are not allowed but the node has them.
        # For features that are allowed, check that their values are allowed.
        for f in node.feats:
            if f in allowed:
                if not node.feats[f] in allowed[f]:
                    self.bug(node, 'Feat' + f + 'Value' + node.feats[f] + 'NotAllowed')
            else:
                self.bug(node, 'Feat' + f + 'NotAllowed')

    def check_required_features(self, node, required):
        """
        We need a list of names of features whose values must not be empty.
        """
        for f in required:
            if not f in node.feats:
                self.bug(node, 'Feat' + f + 'Missing')

    def process_node(self, node):
        # NOUNS ################################################################
        if node.upos == 'NOUN':
            self.check_required_features(node, ['Gender', 'Number', 'Case', 'Polarity'])
            if node.feats['Gender'] == 'Masc':
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
                    self.check_required_features(node, ['PronType', 'Person', 'Number', 'Case'])
                    if node.feats['Person'] == '3':
                        if re.match(r'^(Nom|Voc)$', node.feats['Case']):
                            self.check_required_features(node, ['Gender'])
                            # In PDT, animacy of personal pronouns is distinguished only for Person=3 Case=Nom Gender=Masc Number=Plur ('oni' vs. 'ony').
                            # So we will neither require nor allow it in singular and dual.
                            if node.feats['Gender'] == 'Masc' and node.feats['Number'] == 'Plur':
                                self.check_required_features(node, ['Animacy'])
                                self.check_allowed_features(node, {
                                    'PronType': ['Prs'],
                                    'Person': ['3'],
                                    'Gender': ['Masc'],
                                    'Animacy': ['Anim', 'Inan'],
                                    'Number': ['Plur'],
                                    'Case': ['Nom', 'Voc']
                                })
                            else: # on, ona, ono, ony (Fem Plur)
                                self.check_allowed_features(node, {
                                    'PronType': ['Prs'],
                                    'Person': ['3'],
                                    'Gender': ['Masc', 'Fem', 'Neut'],
                                    'Number': ['Sing', 'Dual', 'Plur'],
                                    'Case': ['Nom', 'Voc']
                                })
                        else: # non-nominatives also have PrepCase
                            # Mostly only two gender groups and no animacy:
                            # Masc,Neut ... jeho, jemu, jej, něm, jím
                            # Fem ... jí, ji, ní
                            # Neut ... je
                            self.check_required_features(node, ['PrepCase'])
                            if node.feats['Number'] == 'Sing':
                                self.check_required_features(node, ['Gender'])
                                self.check_allowed_features(node, {
                                    'PronType': ['Prs'],
                                    'Person': ['3'],
                                    'Gender': ['Masc,Neut', 'Fem', 'Neut'],
                                    'Number': ['Sing'],
                                    'Case': ['Gen', 'Dat', 'Acc', 'Loc', 'Ins'],
                                    'PrepCase': ['Npr', 'Pre']
                                })
                            # No gender in dual and plural:
                            # Plur ... jich, jim, je, nich, jimi
                            else:
                                self.check_allowed_features(node, {
                                    'PronType': ['Prs'],
                                    'Person': ['3'],
                                    'Number': ['Dual', 'Plur'],
                                    'Case': ['Gen', 'Dat', 'Acc', 'Loc', 'Ins'],
                                    'PrepCase': ['Npr', 'Pre']
                                })
                    else: # 1st and 2nd person do not have gender
                        self.check_allowed_features(node, {
                            'PronType': ['Prs'],
                            'Person': ['1', '2', '3'],
                            'Number': ['Sing', 'Dual', 'Plur'],
                            'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                            'Variant': ['Short']
                        })
            else: # PronType není Prs
                # Int,Rel ... kdo, co
                # Rel ... kdož, což, jenž, ješto, jenžto, an
                # Ind ... něco
                # Neg ... nic, nicož
                # kdo, kdož, někdo, nikdo ... Gender=Masc, Animacy=Anim, Case (but no Number; it could be used in the context of any number)
                # jehožto, něhožto, jemužto, němužto ... Gender=Masc,Neut (similarly to non-nominative forms of personal pronoun 'on')
                ###!!! We could make the requirements more precise if we look at the lemma.
                self.check_required_features(node, ['PronType', 'Case'])
                self.check_allowed_features(node, {
                    'PronType': ['Int,Rel', 'Rel', 'Ind', 'Neg'],
                    'Gender': ['Masc', 'Masc,Neut', 'Fem', 'Neut'],
                    'Animacy': ['Anim'],
                    'Number': ['Sing', 'Dual', 'Plur'],
                    'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins'],
                    'PrepCase': ['Npr', 'Pre']
                })
        # DETERMINERS ##########################################################
        elif node.upos == 'DET':
            # Possessive determiners 'jeho' and 'jejich' (formerly 'jich') do not inflect, i.e., no Gender, Number, Case.
            # Note that the possessive determiner 'její' (formerly 'jejie') does inflect, although it also has the lemma 'jeho'.
            if re.match(r'^(jeho|jejich|jich|jehož|jejichž|jichž|jehožto|jejichžto|jichžto)$', node.form.lower()):
                self.check_required_features(node, ['PronType', 'Poss', 'Person', 'Number[psor]'])
                self.check_allowed_features(node, {
                    'PronType': ['Prs', 'Rel'],
                    'Poss': ['Yes'],
                    'Person': ['3'],
                    'Number[psor]': ['Sing', 'Dual', 'Plur'],
                    'Gender[psor]': ['Masc,Neut']
                })
            else:
                # Gender is annotated in all cases in singular, but only in
                # nominative, accusative (and theoretically vocative) in plural.
                # Other cases (Gen, Dat, Loc, Ins) are gender-less: 'těch', 'svým', ...
                # Note that this is not consistent with adjectives, where we
                # disambiguate gender in all cases in plural.
                # Same for animacy (which implies masculine gender).
                self.check_required_features(node, ['PronType', 'Number', 'Case'])
                self.check_allowed_features(node, {
                    'PronType': ['Prs', 'Dem', 'Int,Rel', 'Rel', 'Ind', 'Neg', 'Tot', 'Emp'],
                    'Poss': ['Yes'],
                    'Reflex': ['Yes'],
                    'Person': ['1', '2', '3'],
                    'Number[psor]': ['Sing', 'Dual', 'Plur'],
                    'Gender[psor]': ['Masc,Neut', 'Fem'],
                    'Gender': ['Masc', 'Masc,Neut', 'Fem', 'Fem,Neut', 'Neut'], # non-nominative forms of Masc and Neut are merged; Fem,Neut is e.g. 'vaše' in singular
                    'Animacy': ['Anim', 'Inan'],
                    'Number': ['Sing', 'Dual', 'Plur'],
                    'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Ins']
                })
        # NUMERALS #############################################################
        elif node.upos == 'NUM':
            self.check_required_features(node, ['NumType', 'NumForm'])
            self.check_allowed_features(node, {
                'NumType': ['Card'],
                'NumForm': ['Word', 'Digit', 'Roman'],
                'NumValue': ['1,2,3'],
                'Gender': ['Masc', 'Masc,Neut', 'Fem', 'Fem,Neut', 'Neut'], # similarly to determiners, genders are merged in some slots of the paradigm
                'Animacy': ['Anim', 'Inan'],
                'Number': ['Sing', 'Dual', 'Plur'],
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
                self.check_required_features(node, ['Tense', 'Gender', 'Number', 'Voice', 'Polarity'])
                self.check_allowed_features(node, {
                    'Aspect': ['Imp', 'Perf'],
                    'VerbForm': ['Part'],
                    'Tense': ['Past'],
                    'Voice': ['Act'], # passive participle is ADJ, so we will not encounter it under VERB
                    'Number': ['Sing', 'Dual', 'Plur'],
                    'Gender': ['Masc', 'Fem', 'Neut'],
                    'Animacy': ['Anim', 'Inan'],
                    'Polarity': ['Pos', 'Neg']
                })
            else: # converb
                self.check_required_features(node, ['Tense', 'Number', 'Voice', 'Polarity'])
                self.check_allowed_features(node, {
                    'Aspect': ['Imp', 'Perf'],
                    'VerbForm': ['Conv'],
                    'Tense': ['Past', 'Pres'],
                    'Voice': ['Act'], # passive participle is ADJ, so we will not encounter it under VERB
                    'Number': ['Sing', 'Dual', 'Plur'],
                    'Gender': ['Masc', 'Fem', 'Neut'], # annotated only in singular, and no animacy
                    'Polarity': ['Pos', 'Neg']
                })
        # ADVERBS ##############################################################
        elif node.upos == 'ADV':
            self.check_allowed_features(node, {
                'PronType': ['Dem', 'Int,Rel', 'Ind', 'Neg'],
                'Degree': ['Pos', 'Cmp', 'Sup'],
                'Polarity': ['Pos', 'Neg']
            })
        # ADPOSITIONS ##########################################################
        elif node.upos == 'ADP':
            self.check_allowed_features(node, {
                'AdpType': ['Prep', 'Voc'],
                'Case': ['Gen', 'Dat', 'Acc', 'Loc', 'Ins']
            })
        # THE REST: NO FEATURES ################################################
        else:
            self.check_allowed_features(node, {})
