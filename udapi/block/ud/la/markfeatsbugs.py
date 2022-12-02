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

    def __init__(self, flavio=False, **kwargs):
        """
        Create the ud.la.MarkFeatsBugs block instance.

        Args:
        flavio=1: Accept features as defined by Flavio for treebanks he
            maintains. By default, a more conservative set of features and
            values is expected.
        """
        super().__init__(**kwargs)
        self.flavio = flavio

    def process_node(self, node):
        # NOUNS ################################################################
        if node.upos == 'NOUN':
            rf = ['Gender', 'Number', 'Case']
            af = {
                'Gender': ['Masc', 'Fem', 'Neut'],
                'Number': ['Sing', 'Plur'],
                'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl'],
                'Foreign': ['Yes']}
            if self.flavio:
                rf.append('InflClass')
                af['InflClass'] = ['IndEurA', 'IndEurO', 'IndEurX']
            self.check_required_features(node, rf)
            self.check_allowed_features(node, af)
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
            rf = ['Gender', 'Number', 'Case', 'Degree']
            af = {
                'Gender': ['Masc', 'Fem', 'Neut'],
                'Number': ['Sing', 'Plur'],
                'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl'],
                'Degree': ['Pos', 'Cmp', 'Sup', 'Abs'],
                'Foreign': ['Yes']}
            if self.flavio:
                # Flavio does not use Degree=Pos, hence Degree is not required.
                rf = [f for f in rf if f != 'Degree']
                rf.append('InflClass')
                af['InflClass'] = ['IndEurA', 'IndEurO', 'IndEurX']
            self.check_required_features(node, rf)
            self.check_allowed_features(node, af)
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
                rf = ['PronType', 'Gender', 'Number', 'Case']
                af = {
                    'PronType': ['Dem', 'Int', 'Rel', 'Ind', 'Neg', 'Tot', 'Emp'],
                    'Gender': ['Masc', 'Fem', 'Neut'],
                    'Number': ['Sing', 'Plur'],
                    'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl']}
                if self.flavio:
                    rf.append('InflClass')
                    af['PronType'].append('Con')
                    af['InflClass'] = ['LatPron']
                    af['Form'] = ['Emp']
                self.check_required_features(node, rf)
                self.check_allowed_features(node, af)
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
                self.check_required_features(node, ['NumType', 'NumForm'])
                self.check_allowed_features(node, {
                    'NumType': ['Card'],
                    'NumForm': ['Word']
                })
        # VERBS AND AUXILIARIES ################################################
        elif re.match(r'^(VERB|AUX)$', node.upos):
            rf = ['Aspect', 'VerbForm']
            af = {
                'Aspect': ['Imp', 'Perf', 'Prosp'],
                'VerbForm': ['Inf', 'Fin', 'Part', 'Vnoun'],
                'Polarity': ['Pos', 'Neg']}
            if node.feats['VerbForm'] == 'Fin':
                rf.extend(['Mood', 'Person', 'Number'])
                af['Mood'] = ['Ind', 'Sub', 'Imp']
                af['Person'] = ['1', '2', '3']
                af['Number'] = ['Sing', 'Plur']
                if re.match(r'^(Ind|Sub)$', node.feats['Mood']): # indicative or subjunctive
                    rf.extend(['Voice', 'Tense'])
                    af['Voice'] = ['Act', 'Pass']
                    af['Tense'] = ['Past', 'Imp', 'Pres', 'Fut']
            elif node.feats['VerbForm'] == 'Part':
                rf.extend(['Tense', 'Gender', 'Number', 'Voice'])
                af['Tense'] = ['Past']
                af['Voice'] = ['Act']
                af['Number'] = ['Sing', 'Plur']
                af['Gender'] = ['Masc', 'Fem', 'Neut']
            else: # verbal noun
                rf.extend(['Tense', 'Voice'])
                af['Tense'] = ['Past', 'Pres']
                af['Voice'] = ['Act']
                af['Gender'] = ['Masc', 'Fem', 'Neut']
            if self.flavio:
                # Flavio has killed Tense in his treebanks.
                rf = [f for f in rf if f != 'Tense']
                # Flavio added InflClass but not everywhere, so it is not required.
                af['InflClass'] = ['LatA', 'LatAnom', 'LatE', 'LatI2', 'LatX']
            self.check_required_features(node, rf)
            self.check_allowed_features(node, af)
        # ADVERBS ##############################################################
        elif node.upos == 'ADV':
            if node.feats['PronType'] != '':
                # Pronominal adverbs are neither compared nor negated.
                self.check_allowed_features(node, {
                    'PronType': ['Dem', 'Int', 'Rel', 'Ind', 'Neg', 'Tot'],
                    'AdvType': ['Loc']
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
