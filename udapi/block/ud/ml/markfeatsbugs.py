"""
Block to identify missing or ill-valued features in Malayalam. Any bugs that it
finds will be saved in the MISC column as a Bug attribute, which can be later
used in filters and highlighted in text output.

Usage: cat *.conllu | udapy -HAMX layout=compact ud.ml.MarkFeatsBugs > bugs.html
Windows: python udapy read.Conllu files="a.conllu,b.conllu" ud.ml.MarkFeatsBugs write.TextModeTreesHtml files="bugs.html" marked_only=1 layout=compact attributes=form,lemma,upos,xpos,feats,deprel,misc
"""
import udapi.block.ud.markfeatsbugs
import logging
import re

class MarkFeatsBugs(udapi.block.ud.markfeatsbugs.MarkFeatsBugs):

    def process_node(self, node):
        # NOUNS AND PROPER NOUNS ###############################################
        if re.match(r'^(NOUN|PROPN)$', node.upos):
            self.check_required_features(node, ['Animacy', 'Number', 'Case'])
            self.check_allowed_features(node, {
                'Animacy': ['Anim', 'Inan'],
                'Number': ['Sing', 'Plur'],
                'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl', 'Ins', 'Cmp'],
                'Foreign': ['Yes']})
        # ADJECTIVES ###########################################################
        elif node.upos == 'ADJ':
            self.check_allowed_features(node, {
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
                        'Case': ['Gen', 'Dat', 'Acc', 'Loc', 'Abl', 'Ins', 'Cmp']
                    })
                else: # not reflexive
                    if node.feats['Person'] == '3': # അവൻ avan, അവൾ avaḷ, അത് at, അവർ avaṟ
                        if node.feats['Number'] == 'Sing':
                            self.check_required_features(node, ['PronType', 'Person', 'Deixis', 'Gender', 'Number', 'Case'])
                            self.check_allowed_features(node, {
                                'PronType': ['Prs'],
                                'Person': ['3'],
                                'Deixis': ['Prox', 'Remt'],
                                'Gender': ['Masc', 'Fem', 'Neut'],
                                'Number': ['Sing'],
                                'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl', 'Ins', 'Cmp']
                            })
                        else: # plural pronouns do not distinguish gender
                            self.check_required_features(node, ['PronType', 'Person', 'Deixis', 'Number', 'Case'])
                            self.check_allowed_features(node, {
                                'PronType': ['Prs'],
                                'Person': ['3'],
                                'Deixis': ['Prox', 'Remt'],
                                'Number': ['Plur'],
                                'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl', 'Ins', 'Cmp']
                            })
                    else: # 1st and 2nd person do not have gender: ഞാൻ ñān, നീ nī
                        self.check_required_features(node, ['PronType', 'Person', 'Number', 'Case'])
                        self.check_allowed_features(node, {
                            'PronType': ['Prs'],
                            'Person': ['1', '2'],
                            'Number': ['Sing', 'Plur'],
                            'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl', 'Ins', 'Cmp']
                        })
            else: # not personal
                self.check_required_features(node, ['PronType', 'Case'])
                self.check_allowed_features(node, {
                    'PronType': ['Dem', 'Int'],
                    'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl', 'Ins', 'Cmp']
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
                    'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl', 'Ins', 'Cmp']
                })
            else:
                self.check_required_features(node, ['PronType', 'Gender', 'Number', 'Case'])
                self.check_allowed_features(node, {
                    'PronType': ['Dem', 'Int', 'Rel', 'Ind', 'Neg', 'Tot', 'Emp'],
                    'Gender': ['Masc', 'Fem', 'Neut'],
                    'Number': ['Sing', 'Plur'],
                    'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl', 'Ins', 'Cmp']
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
                    'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl', 'Ins', 'Cmp']
                })
        # VERBS ################################################################
        elif node.upos == 'VERB':
            self.check_required_features(node, ['VerbForm', 'Voice'])
            if node.feats['VerbForm'] == 'Inf':
                self.check_allowed_features(node, {
                    'VerbForm': ['Inf'],
                    'Polarity': ['Pos', 'Neg'],
                    'Voice': ['Act', 'Pass', 'Cau']
                })
            elif node.feats['VerbForm'] == 'Fin':
                if node.feats['Mood'] == 'Imp':
                    self.check_required_features(node, ['Mood', 'Voice'])
                    self.check_allowed_features(node, {
                        'Aspect': ['Imp', 'Perf', 'Prog'],
                        'VerbForm': ['Fin'],
                        'Mood': ['Imp'],
                        'Polarity': ['Pos', 'Neg'],
                        'Voice': ['Act', 'Pass', 'Cau']
                    })
                else:
                    self.check_required_features(node, ['Mood', 'Tense', 'Voice'])
                    self.check_allowed_features(node, {
                        'Aspect': ['Imp', 'Perf', 'Prog'],
                        'VerbForm': ['Fin'],
                        'Mood': ['Ind', 'Nec'],
                        'Tense': ['Past', 'Imp', 'Pres', 'Fut'], # only in indicative
                        'Polarity': ['Pos', 'Neg'],
                        'Voice': ['Act', 'Pass', 'Cau']
                    })
            elif node.feats['VerbForm'] == 'Part':
                self.check_required_features(node, ['Tense', 'Voice'])
                self.check_allowed_features(node, {
                    'Aspect': ['Imp', 'Perf', 'Prog'],
                    'VerbForm': ['Part'],
                    'Tense': ['Past'],
                    'Polarity': ['Pos', 'Neg'],
                    'Voice': ['Act', 'Pass', 'Cau']
                })
            else: # verbal noun
                self.check_required_features(node, ['Tense', 'Voice'])
                self.check_allowed_features(node, {
                    'Aspect': ['Imp', 'Perf', 'Prog'],
                    'VerbForm': ['Vnoun'],
                    'Tense': ['Past', 'Pres'],
                    'Gender': ['Masc', 'Fem', 'Neut'],
                    'Polarity': ['Pos', 'Neg'],
                    'Voice': ['Act', 'Pass', 'Cau'],
                })
        # AUXILIARIES ##########################################################
        elif node.upos == 'AUX':
            self.check_required_features(node, ['VerbForm'])
            if node.feats['Mood'] == 'Imp':
                self.check_required_features(node, ['Mood'])
                self.check_allowed_features(node, {
                    'Aspect': ['Imp', 'Perf', 'Prog'],
                    'VerbForm': ['Fin'],
                    'Mood': ['Imp'],
                    'Polarity': ['Pos', 'Neg']
                })
            else: # indicative or subjunctive
                self.check_required_features(node, ['Mood', 'Tense'])
                self.check_allowed_features(node, {
                    'Aspect': ['Imp', 'Perf', 'Prog'],
                    'VerbForm': ['Fin'],
                    'Mood': ['Ind', 'Sub'],
                    'Tense': ['Past', 'Imp', 'Pres', 'Fut'], # only in indicative
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
