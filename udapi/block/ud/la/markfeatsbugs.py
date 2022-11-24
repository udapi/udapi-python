"""
Block to identify missing or ill-valued features in Latin. Any bugs that it
finds will be saved in the MISC column as a Bug attribute, which can be later
used in filters and highlighted in text output.

Usage: cat *.conllu | udapy -HAMX layout=compact ud.la.MarkFeatsBugs > bugs.html
Windows: python udapy read.Conllu files="a.conllu,b.conllu" ud.la.MarkFeatsBugs write.TextModeTreesHtml files="bugs.html" marked_only=1 layout=compact attributes=form,lemma,upos,xpos,feats,deprel,misc
"""
import udapi.block.ud.markfeatsbugs
import logging
import re

class MarkFeatsBugs(udapi.block.ud.markfeatsbugs.MarkFeatsBugs):

    def process_node(self, node):
        # NOUNS ################################################################
        if node.upos == 'NOUN':
            self.check_required_features(node, ['Gender', 'Number', 'Case'])
            self.check_allowed_features(node, {
                'Gender': ['Masc', 'Fem', 'Neut'],
                'Number': ['Sing', 'Plur'],
                'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl'],
                'Foreign': ['Yes']})
        # PROPER NOUNS #########################################################
        elif node.upos == 'PROPN':
            self.check_required_features(node, ['Gender', 'Number', 'Case'])
            self.check_allowed_features(node, {
                'Gender': ['Masc', 'Fem', 'Neut'],
                'Number': ['Sing', 'Plur'],
                'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl'],
                'NameType': ['Giv', 'Sur', 'Geo'],
                'Foreign': ['Yes']})
        # ADJECTIVES ###########################################################
        elif node.upos == 'ADJ':
            self.check_required_features(node, ['Gender', 'Number', 'Case', 'Degree'])
            self.check_allowed_features(node, {
                'Gender': ['Masc', 'Fem', 'Neut'],
                'Number': ['Sing', 'Plur'],
                'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl'],
                'Degree': ['Pos', 'Cmp', 'Sup'],
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
                        'Case': ['Gen', 'Dat', 'Acc', 'Loc', 'Abl']
                    })
                else: # not reflexive
                    if node.feats['Person'] == '3': # on, ona, ono, oni, ony
                        self.check_required_features(node, ['PronType', 'Person', 'Gender', 'Number', 'Case'])
                        self.check_allowed_features(node, {
                            'PronType': ['Prs'],
                            'Person': ['3'],
                            'Gender': ['Masc', 'Fem', 'Neut'],
                            'Number': ['Sing', 'Plur'],
                            'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl']
                        })
                    else: # 1st and 2nd person do not have gender: já, ty
                        self.check_required_features(node, ['PronType', 'Person', 'Number', 'Case'])
                        self.check_allowed_features(node, {
                            'PronType': ['Prs'],
                            'Person': ['1', '2'],
                            'Number': ['Sing', 'Plur'],
                            'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl']
                        })
        # DETERMINERS ##########################################################
        elif node.upos == 'DET':
            if node.feats['Poss'] == 'Yes': # 'můj', 'tvůj', 'svůj'
                self.check_required_features(node, ['PronType', 'Poss', 'Person', 'Gender', 'Number', 'Case'])
                self.check_allowed_features(node, {
                    'PronType': ['Prs'],
                    'Poss': ['Yes'],
                    'Person': ['1', '2', '3'],
                    'Gender': ['Masc', 'Fem', 'Neut'],
                    'Number': ['Sing', 'Plur'],
                    'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl']
                })
            else:
                self.check_required_features(node, ['PronType', 'Gender', 'Number', 'Case'])
                self.check_allowed_features(node, {
                    'PronType': ['Dem', 'Int', 'Rel', 'Ind', 'Neg', 'Tot', 'Emp'],
                    'Gender': ['Masc', 'Fem', 'Neut'],
                    'Number': ['Sing', 'Plur'],
                    'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl']
                })
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
                self.check_required_features(node, ['NumType', 'NumForm', 'Number', 'Case'])
                self.check_allowed_features(node, {
                    'NumType': ['Card'],
                    'NumForm': ['Word'],
                    'Number': ['Plur'],
                    'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl']
                })
        # VERBS AND AUXILIARIES ################################################
        elif re.match(r'^(VERB|AUX)$', node.upos):
            self.check_required_features(node, ['Aspect', 'VerbForm'])
            if node.feats['VerbForm'] == 'Inf':
                self.check_allowed_features(node, {
                    'Aspect': ['Imp', 'Perf', 'Prosp'],
                    'VerbForm': ['Inf'],
                    'Polarity': ['Pos', 'Neg']
                })
            elif node.feats['VerbForm'] == 'Fin':
                if node.feats['Mood'] == 'Imp':
                    self.check_required_features(node, ['Mood', 'Person', 'Number'])
                    self.check_allowed_features(node, {
                        'Aspect': ['Imp', 'Perf', 'Prosp'],
                        'VerbForm': ['Fin'],
                        'Mood': ['Imp'],
                        'Person': ['1', '2', '3'],
                        'Number': ['Sing', 'Plur'],
                        'Polarity': ['Pos', 'Neg']
                    })
                else: # indicative or subjunctive
                    self.check_required_features(node, ['Mood', 'Voice', 'Tense', 'Person', 'Number'])
                    self.check_allowed_features(node, {
                        'Aspect': ['Imp', 'Perf', 'Prosp'],
                        'VerbForm': ['Fin'],
                        'Mood': ['Ind', 'Sub'],
                        'Tense': ['Past', 'Imp', 'Pres', 'Fut'], # only in indicative
                        'Voice': ['Act'],
                        'Person': ['1', '2', '3'],
                        'Number': ['Sing', 'Plur'],
                        'Polarity': ['Pos', 'Neg']
                    })
            elif node.feats['VerbForm'] == 'Part':
                self.check_required_features(node, ['Tense', 'Gender', 'Number', 'Voice'])
                self.check_allowed_features(node, {
                    'Aspect': ['Imp', 'Perf', 'Prosp'],
                    'VerbForm': ['Part'],
                    'Tense': ['Past'],
                    'Voice': ['Act'], # passive participle is ADJ, so we will not encounter it under VERB
                    'Number': ['Sing', 'Plur'],
                    'Gender': ['Masc', 'Fem', 'Neut'],
                    'Polarity': ['Pos', 'Neg']
                })
            else: # verbal noun
                self.check_required_features(node, ['Tense', 'Number', 'Voice'])
                self.check_allowed_features(node, {
                    'Aspect': ['Imp', 'Perf', 'Prosp'],
                    'VerbForm': ['Vnoun'],
                    'Tense': ['Past', 'Pres'],
                    'Voice': ['Act'],
                    'Number': ['Sing', 'Plur'],
                    'Gender': ['Masc', 'Fem', 'Neut'], # annotated only in singular
                    'Polarity': ['Pos', 'Neg']
                })
        # ADVERBS ##############################################################
        elif node.upos == 'ADV':
            if node.feats['PronType'] != '':
                # Pronominal adverbs are neither compared nor negated.
                self.check_allowed_features(node, {
                    'PronType': ['Dem', 'Int', 'Rel', 'Ind', 'Neg', 'Tot']
                })
            else:
                # The remaining adverbs are neither pronominal, nor compared or
                # negated.
                self.check_allowed_features(node, {})
        # PARTICLES ############################################################
        elif node.upos == 'PART':
            self.check_allowed_features(node, {
                'Polarity': ['Neg']
            })
        # THE REST: NO FEATURES ################################################
        else:
            self.check_allowed_features(node, {})
