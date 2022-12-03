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
        rf = []
        af = {}
        # NOUNS ################################################################
        if node.upos == 'NOUN':
            if not node.feats['Abbr'] == 'Yes':
                rf = ['Gender', 'Number', 'Case']
            af = {
                'Gender': ['Masc', 'Fem', 'Neut'],
                'Number': ['Sing', 'Plur'],
                'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl'],
                'Degree': ['Dim'],
                'Abbr': ['Yes'],
                'Foreign': ['Yes']}
            if self.flavio:
                # Flavio added InflClass but not everywhere, so it is not required.
                af['InflClass'] = ['IndEurA', 'IndEurE', 'IndEurI', 'IndEurO', 'IndEurU', 'IndEurX']
            self.check_required_features(node, rf)
            self.check_allowed_features(node, af)
        # PROPER NOUNS #########################################################
        elif node.upos == 'PROPN':
            if not node.feats['Abbr'] == 'Yes':
                rf = ['Gender', 'Number', 'Case']
            af = {
                'Gender': ['Masc', 'Fem', 'Neut'],
                'Number': ['Sing', 'Plur'],
                'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl'],
                'NameType': ['Giv', 'Sur', 'Geo'],
                'Abbr': ['Yes'],
                'Foreign': ['Yes']}
            if self.flavio:
                # Flavio added InflClass but not everywhere, so it is not required.
                af['InflClass'] = ['IndEurA', 'IndEurE', 'IndEurI', 'IndEurO', 'IndEurU', 'IndEurX']
                af['Proper'] = ['Yes']
            self.check_required_features(node, rf)
            self.check_allowed_features(node, af)
        # ADJECTIVES ###########################################################
        elif node.upos == 'ADJ':
            if not node.feats['Abbr'] == 'Yes':
                rf = ['Gender', 'Number', 'Case', 'Degree']
            af = {
                'NumType': ['Ord', 'Dist'],
                'Gender': ['Masc', 'Fem', 'Neut'],
                'Number': ['Sing', 'Plur'],
                'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl'],
                'Degree': ['Pos', 'Cmp', 'Sup', 'Abs'],
                'Abbr': ['Yes'],
                'Foreign': ['Yes']}
            if self.flavio:
                # Flavio does not use Degree=Pos, hence Degree is not required.
                rf = [f for f in rf if f != 'Degree']
                # Flavio added InflClass but not everywhere, so it is not required.
                af['InflClass'] = ['IndEurA', 'IndEurE', 'IndEurI', 'IndEurO', 'IndEurU', 'IndEurX']
                af['Compound'] = ['Yes']
                af['Proper'] = ['Yes']
            self.check_required_features(node, rf)
            self.check_allowed_features(node, af)
        # PRONOUNS #############################################################
        elif node.upos == 'PRON':
            rf = ['PronType', 'Case']
            af = {
                'PronType': ['Prs', 'Rel', 'Ind'],
                'Case':     ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl']
            }
            if node.feats['PronType'] == 'Prs':
                af['Reflex'] = ['Yes']
                if node.feats['Reflex'] == 'Yes': # seipsum, se
                    # seipsum has gender and number but se does not, so it is not required
                    af['Gender'] = ['Masc']
                    af['Number'] = ['Sing']
                    af['Person'] = ['3']
                    af['Case'] = ['Gen', 'Dat', 'Acc', 'Loc', 'Abl']
                else: # not reflexive: ego, tu, is, nos
                    rf.extend(['Person', 'Number'])
                    af['Person'] = ['1', '2', '3']
                    af['Number'] = ['Sing', 'Plur']
                    # 1st and 2nd person do not have gender
                    if node.feats['Person'] == '3': # is, id
                        rf.append('Gender')
                        af['Gender'] = ['Masc', 'Fem', 'Neut']
            elif re.match(r'^(Rel|Ind)$', node.feats['PronType']):
                rf.extend(['Gender', 'Number'])
                af['Gender'] = ['Masc', 'Fem', 'Neut']
                af['Number'] = ['Sing', 'Plur']
            if self.flavio:
                # Flavio added InflClass but not everywhere, so it is not required.
                af['InflClass'] = ['LatAnom', 'LatPron']
            self.check_required_features(node, rf)
            self.check_allowed_features(node, af)
        # DETERMINERS ##########################################################
        elif node.upos == 'DET':
            rf = ['PronType', 'Gender', 'Number', 'Case']
            af = {
                'Gender': ['Masc', 'Fem', 'Neut'],
                'Number': ['Sing', 'Plur'],
                'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl']}
            if node.feats['Poss'] == 'Yes': # 'meus', 'tuus', 'suus', 'noster'
                rf.extend(['Poss', 'Person[psor]'])
                af['PronType'] = ['Prs']
                af['Poss'] = 'Yes'
                af['Person[psor]'] = ['1', '2', '3']
                af['Reflex'] = ['Yes']
                # The possessor's number is distinguished in the first and second person (meus vs. noster) but not in the third person (suus).
                if node.feats['Person[psor]'] != '3':
                    rf.append('Number[psor]')
                    af['Number[psor]'] = ['Sing', 'Plur']
            else:
                af['PronType'] = ['Dem', 'Rel', 'Ind', 'Tot', 'Con']
            if self.flavio:
                # Flavio added InflClass but not everywhere, so it is not required.
                af['InflClass'] = ['IndEurA', 'IndEurI', 'IndEurO', 'LatPron']
                af['Form'] = ['Emp']
            self.check_required_features(node, rf)
            self.check_allowed_features(node, af)
        # NUMERALS #############################################################
        elif node.upos == 'NUM':
            rf = ['NumType', 'NumForm']
            af = {
                'NumType': ['Card'],
                'NumForm': ['Word', 'Roman', 'Digit']
            }
            # Arabic digits and Roman numerals do not have inflection features.
            if not re.match(r'^(Digit|Roman)$', node.feats['NumForm']):
                af['Gender'] = ['Masc', 'Fem', 'Neut']
                af['Number'] = ['Sing', 'Plur']
                af['Case'] = ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl']
            if self.flavio:
                # Flavio added InflClass but not everywhere, so it is not required.
                af['InflClass'] = ['IndEurA', 'IndEurI', 'IndEurO', 'LatPron']
            self.check_required_features(node, rf)
            self.check_allowed_features(node, af)
        # VERBS AND AUXILIARIES ################################################
        elif re.match(r'^(VERB|AUX)$', node.upos):
            rf = ['VerbForm']
            af = {
                'VerbForm': ['Inf', 'Fin', 'Part', 'Vnoun'],
                'Polarity': ['Pos', 'Neg']}
            # Main verbs have aspect but auxiliaries don't.
            if node.upos == 'VERB':
                rf.append('Aspect')
                af['Aspect'] = ['Imp', 'Perf', 'Prosp']
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
                rf.extend(['Tense', 'Gender', 'Number', 'Voice', 'Case'])
                af['Tense'] = ['Past']
                af['Voice'] = ['Act', 'Pass']
                af['Number'] = ['Sing', 'Plur']
                af['Gender'] = ['Masc', 'Fem', 'Neut']
                af['Case'] = ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl']
                af['Degree'] = ['Abs']
            elif node.feats['VerbForm'] == 'Vnoun':
                rf.extend(['Tense', 'Voice'])
                af['Tense'] = ['Past', 'Pres']
                af['Voice'] = ['Act', 'Pass']
                af['Gender'] = ['Masc', 'Fem', 'Neut']
            # else: nothing to be added form VerbForm=Inf
            if self.flavio:
                # Flavio has killed Tense in his treebanks.
                rf = [f for f in rf if f != 'Tense']
                # Flavio added InflClass but not everywhere, so it is not required.
                af['InflClass'] = ['LatA', 'LatAnom', 'LatE', 'LatI2', 'LatX']
                if node.feats['VerbForm'] == 'Part':
                    af['InflClass[nominal]'] = ['IndEurA', 'IndEurI', 'IndEurO']
            self.check_required_features(node, rf)
            self.check_allowed_features(node, af)
        # ADVERBS ##############################################################
        elif node.upos == 'ADV':
            af = {
                'AdvType':  ['Loc', 'Tim'],
                'PronType': ['Dem', 'Int', 'Rel', 'Ind', 'Neg', 'Tot', 'Con'],
                'Degree':   ['Pos', 'Cmp', 'Sup', 'Abs']
            }
            if self.flavio:
                af['Compound'] = 'Yes'
                af['Form'] = 'Emp'
            self.check_allowed_features(node, af)
        # PARTICLES ############################################################
        elif node.upos == 'PART':
            af = {
                'PartType': ['Int'],
                'Polarity': ['Neg']
            }
            if self.flavio:
                af['Form'] = 'Emp'
            self.check_allowed_features(node, af)
        # THE REST: NO FEATURES ################################################
        else:
            self.check_allowed_features(node, {})
