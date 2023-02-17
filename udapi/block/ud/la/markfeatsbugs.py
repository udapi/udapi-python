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
        # PROIEL-specific: greek words without features
        if node.lemma == 'greek.expression':
            pass
        # NOUNS ################################################################
        elif node.upos == 'NOUN':
            if node.feats['Case'] and not node.feats['Abbr'] == 'Yes': # abbreviated or indeclinable nouns
                rf = ['Gender', 'Number', 'Case']
            af = {
                'Gender': ['Masc', 'Fem', 'Neut'],
                'Number': ['Sing', 'Plur'],
                'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl'],
                'Degree': ['Dim'],
                'Abbr': ['Yes'],
                'Foreign': ['Yes'],
                'VerbForm': ['Part']}
            if self.flavio:
                # Flavio added InflClass but not everywhere, so it is not required.
                af['InflClass'] = ['IndEurA', 'IndEurE', 'IndEurI', 'IndEurO', 'IndEurU', 'IndEurX']
                af['Proper'] = ['Yes']
                af['Compound'] = ['Yes']
                af['NameType'] = ['Ast', 'Cal', 'Com', 'Geo', 'Giv', 'Let', 'Lit', 'Met', 'Nat', 'Rel', 'Sur', 'Oth']
            self.check_required_features(node, rf)
            self.check_allowed_features(node, af)
        # PROPER NOUNS #########################################################
        elif node.upos == 'PROPN':
            if not node.feats['Abbr'] == 'Yes' and node.feats['Case']: # abbreviated and indeclinable nouns
                rf = ['Gender', 'Number', 'Case']
            af = {
                'Gender': ['Masc', 'Fem', 'Neut'],
                'Number': ['Sing', 'Plur'],
                'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl'],
                'Abbr': ['Yes'],
                'Foreign': ['Yes']}
            if self.flavio:
                af['Compound'] = 'Yes'
                af['NameType'] = ['Ast', 'Cal', 'Com', 'Geo', 'Giv', 'Let', 'Lit', 'Met', 'Nat', 'Rel', 'Sur', 'Oth']
                if not node.feats['Abbr'] == 'Yes' and node.feats['Case']:
                    af['InflClass'] = ['IndEurA', 'IndEurE', 'IndEurI', 'IndEurO', 'IndEurU', 'IndEurX']
            self.check_required_features(node, rf)
            self.check_allowed_features(node, af)
        # ADJECTIVES ###########################################################
        elif node.upos == 'ADJ':
            if not node.feats['Abbr'] == 'Yes' and node.feats['Case']:
                rf = ['Gender', 'Number', 'Case']
            af = {
                'NumType': ['Ord', 'Dist'],
                'Gender': ['Masc', 'Fem', 'Neut'],
                'Number': ['Sing', 'Plur'],
                'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl'],
                'Degree': ['Cmp', 'Sup', 'Abs'],
                'Abbr': ['Yes'],
                'Foreign': ['Yes'],
                'Polarity': ['Neg'],
                'VerbForm': ['Part']}
            if self.flavio:
                # Flavio added InflClass but not everywhere, so it is not required.
                af['InflClass'] = ['IndEurA', 'IndEurE', 'IndEurI', 'IndEurO', 'IndEurU', 'IndEurX']
                af['Compound'] = ['Yes']
                af['Proper'] = ['Yes']
                af['Degree'].append('Dim')
                af['NameType'] = ['Ast', 'Cal', 'Com', 'Geo', 'Giv', 'Let', 'Lit', 'Met', 'Nat', 'Rel', 'Sur', 'Oth']
            self.check_required_features(node, rf)
            self.check_allowed_features(node, af)
        # PRONOUNS #############################################################
        elif node.upos == 'PRON':
            rf = ['PronType', 'Case']
            af = {
               'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl'],
               'Proper': ['Yes'],
               'Compound': ['Yes'],
               'Polarity': ['Neg']
            }
            if node.feats['PronType'] == 'Prs':
                af['Reflex'] = ['Yes']
                if node.feats['Reflex'] == 'Yes': # seipsum, se
                    rf.extend(['Person'])
                    # seipsum has gender and number but se does not, so it is not required
                    af['Gender'] = ['Masc', 'Fem', 'Neut']
                    af['Number'] = ['Sing', 'Plur']
                    af['Person'] = ['3']
                    af['Case'] = ['Nom', 'Gen', 'Dat', 'Acc', 'Loc', 'Abl']
                else: # not reflexive: ego, tu, is, nos
                    rf.extend(['Person', 'Number'])
                    af['Person'] = ['1', '2', '3']
                    af['Number'] = ['Sing', 'Plur']
                    # 1st and 2nd person do not have gender
                    if node.feats['Person'] == '3': # is, id
                        rf.append('Gender')
                        af['Gender'] = ['Masc', 'Fem', 'Neut']
            elif re.match(r'^(Rel|Int)$', node.feats['PronType']):
                rf.extend(['Gender', 'Number'])
                af['Gender'] = ['Masc', 'Fem', 'Neut']
                af['Number'] = ['Sing', 'Plur']
            elif node.feats['PronType'] == 'Ind':
                rf = [f for f in rf if f != 'Case']
                af['Gender'] = ['Masc', 'Fem', 'Neut']
                af['Number'] = ['Sing', 'Plur']
            # lexical check of PronTypes
            af['PronType'] = []
            if node.lemma in ['is', 'ego', 'tu', 'sui', 'seipsum', 'nos', 'uos', 'vos', 'tumetipse', 'nosmetipse']:
                af['PronType'].append('Prs')
            elif node.lemma in ['quis', 'aliquis', 'nihil', 'nemo', 'quivis', 'qui']:
                af['PronType'].append('Ind')
            elif node.lemma in ['inuicem', 'invicem']:
                af['PronType'].append('Rcp')
                rf.remove('Case')
            if node.lemma in ['quicumque', 'qui', 'quisquis']:
                af['PronType'].append('Rel')
            if node.lemma in ['qui', 'quis', 'quisnam', 'ecquis', 'ecqui']:
                af['PronType'].append('Int')
            if self.flavio:
                # Flavio added InflClass but not everywhere, so it is not required.
                af['InflClass'] = ['LatAnom', 'LatPron']
                af['Compound'] = ['Yes']
                af['Polarity'] = ['Neg']
                af['Form'] = ['Emp']
            self.check_required_features(node, rf)
            self.check_allowed_features(node, af)
        # DETERMINERS ##########################################################
        elif node.upos == 'DET':
            rf = ['PronType']
            if node.feats['Case']:
                rf.extend(['Gender', 'Number', 'Case'])
            af = {
                'Gender': ['Masc', 'Fem', 'Neut'],
                'Number': ['Sing', 'Plur'],
                'Case': ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl'],
                'Degree': ['Cmp', 'Abs', 'Sup'],
                'Polarity': ['Neg'],
                'Proper': ['Yes'],
                'PronType': []
                }
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
            if node.feats['PronType'] == 'Ind':
                af['NumType'] = ['Card']
            # lexical check of PronTypes
            if node.lemma in ['suus', 'meus', 'noster', 'tuus', 'uester', 'vester', 'voster']:
                if not af['PronType'] == ['Prs']:
                    af['PronType'].append('Prs')
            elif node.lemma in ['aliquot', 'quidam', 'quispiam', 'quivis', 'nullus', 'nonnullus', 'aliqui', 'qui', 'quilibet', 'quantuslibet', 'unus', 'uterque', 'ullus', 'multus', 'quisque', 'paucus', 'complures', 'quamplures', 'quicumque', 'reliquus', 'plerusque', 'aliqualis', 'quisquam', 'qualiscumque']:
                af['PronType'].append('Ind')
            elif node.lemma in ['omnis', 'totus', 'ambo', 'cunctus', 'unusquisque', 'uniuersus']:
                af['PronType'].append('Tot')
            if node.lemma in ['quantus', 'qualis', 'quicumque', 'quot', 'quotus', 'quotquot']:
                af['PronType'].append('Rel')
            elif node.lemma in ['qui', 'quantus', 'quot']:
                af['PronType'].append('Int')
            elif node.lemma in ['hic', 'ipse', 'ille', 'tantus', 'talis', 'is', 'iste', 'eiusmodi', 'huiusmodi', 'idem', 'totidem', 'tot']:
                af['PronType'].append('Dem')
            elif node.lemma in ['alius', 'alter', 'solus', 'ceterus', 'alteruter', 'neuter', 'uter']:
                af['PronType'].append('Con')
            if self.flavio:
                # Flavio added InflClass but not everywhere, so it is not required.
                af['InflClass'] = ['IndEurA', 'IndEurI', 'IndEurO', 'IndEurX', 'LatPron']
                af['Compound'] = ['Yes']
                af['Form'] = ['Emp']
                af['NumType'] = ['Card']
                af['Degree'].append('Dim')
                if re.match(r'^(unus|ambo)', node.lemma):
                    af['NumValue'] = ['1', '2']
            self.check_required_features(node, rf)
            self.check_allowed_features(node, af)
        # NUMERALS #############################################################
        elif node.upos == 'NUM':
            rf = ['NumType', 'NumForm']
            af = {
                'NumType': ['Card'],
                'NumForm': ['Word', 'Roman', 'Digit'],
                'Proper': ['Yes']}
            # Arabic digits and Roman numerals do not have inflection features.
            if not re.match(r'^(Digit|Roman)$', node.feats['NumForm']):
                af['Gender'] = ['Masc', 'Fem', 'Neut']
                af['Number'] = ['Sing', 'Plur']
                af['Case'] = ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl']
            if self.flavio:
                # Flavio added InflClass but not everywhere, so it is not required. # e.g. duodecim
                af['InflClass'] = ['IndEurA', 'IndEurI', 'IndEurO', 'LatPron']
            self.check_required_features(node, rf)
            self.check_allowed_features(node, af)
        # VERBS AND AUXILIARIES ################################################
        elif re.match(r'^(VERB|AUX)$', node.upos):
            rf = ['VerbForm', 'Aspect']
            af = {
                'VerbForm': ['Inf', 'Fin', 'Part', 'Conv'],
                'Aspect': ['Imp', 'Inch', 'Perf', 'Prosp'],
                'Polarity': ['Neg'],
                'Typo': ['Yes']
                }
            if node.feats['VerbForm'] not in ['Part', 'Conv']:
                rf.append('Tense')
                af['Tense'] = ['Past', 'Pqp', 'Pres', 'Fut']
            if node.upos == 'VERB':
                rf.append('Voice')
                af['Voice'] = ['Act', 'Pass']
            if node.feats['VerbForm'] == 'Fin': # imperative, indicative or subjunctive
                rf.extend(['Mood', 'Person', 'Number'])
                af['Mood'] = ['Ind', 'Sub', 'Imp']
                af['Person'] = ['1', '2', '3']
                af['Number'] = ['Sing', 'Plur']
            elif node.feats['VerbForm'] == 'Part':
                rf.extend(['Gender', 'Number', 'Case'])
                af['Number'] = ['Sing', 'Plur'] if node.misc['TraditionalMood'] != 'Gerundium' else ['Sing']
                af['Gender'] = ['Masc', 'Fem', 'Neut'] if node.misc['TraditionalMood'] != 'Gerundium' else ['Neut']
                af['Case'] = ['Nom', 'Gen', 'Dat', 'Acc', 'Voc', 'Loc', 'Abl']
                af['Degree'] = ['Abs', 'Cmp']
                if node.misc['TraditionalMood'].startswith('Gerundi'):
                    af['Voice'] = ['Pass']
                    af['Aspect'] = 'Prosp'
            elif node.feats['VerbForm'] == 'Conv':
                rf.extend(['Case', 'Gender', 'Number'])
                af['Case'] = ['Abl', 'Acc']
                af['Gender'] = ['Masc']
                af['Number'] = ['Sing']
                af['Voice'] = ['Act']
            elif node.feats['VerbForm'] == 'Inf':
                af['Tense'].remove('Pqp')
            if self.flavio:
                # Flavio added InflClass but not everywhere, so it is not required.
                af['InflClass'] = ['LatA', 'LatAnom', 'LatE', 'LatI', 'LatI2', 'LatX']
                if 'Degree' in af:
                    af['Degree'].append('Dim')
                else:
                    af['Degree'] = ['Dim']
                af['Compound'] = ['Yes']
                af['Proper'] = ['Yes']
                if re.match(r'^(Part|Conv)$', node.feats['VerbForm']):
                    af['InflClass[nominal]'] = ['IndEurA', 'IndEurI', 'IndEurO', 'IndEurU']
            self.check_required_features(node, rf)
            self.check_allowed_features(node, af)
        # ADVERBS ##############################################################
        elif node.upos == 'ADV':
            af = {
                'AdvType': ['Loc', 'Tim'],
                'PronType': ['Dem', 'Int', 'Rel', 'Ind', 'Neg', 'Tot', 'Con'],
                'Degree': ['Pos', 'Cmp', 'Sup', 'Abs'],
                'NumType': ['Card', 'Ord'], # e.g., primum
                'Polarity': ['Neg']
            }
            if self.flavio:
                af['Compound'] = ['Yes']
                af['Form'] = ['Emp']
                af['VerbForm'] = ['Part']
                af['Degree'].append('Dim')
            self.check_allowed_features(node, af)
        # PARTICLES ############################################################
        elif node.upos == 'PART':
            af = {
                'PartType': ['Int', 'Emp'],
                'Polarity': ['Neg']
            }
            if self.flavio:
                af['Form'] = ['Emp']
                af['PronType'] = ['Dem']
            self.check_allowed_features(node, af)
        # CONJUNCTIONS #########################################################
        elif re.match(r'^[CS]CONJ$', node.upos):
            af = {
            'PronType': ['Rel', 'Con'],
            'Polarity': ['Neg'],
            'Compound': ['Yes']}
            if self.flavio:
                af['Compound'] = ['Yes']
                af['Form'] = ['Emp']
                af['VerbForm'] = ['Fin']
                af['NumType'] = ['Card']
            self.check_allowed_features(node, af)
        # ADPOSITIONS ##########################################################
        elif node.upos == 'ADP':
            rf = ['AdpType']
            af = {
                'AdpType': ['Prep', 'Post'],
                'Abbr': ['Yes']
            }
            if self.flavio:
                af['VerbForm'] = ['Part'],
                af['Proper'] = ['Yes']
            self.check_allowed_features(node, af)
        # THE REST: NO FEATURES ################################################
        else:
            self.check_allowed_features(node, {})
