"""
Block to identify missing or ill-valued features in Malayalam. Any bugs that it
finds will be saved in the MISC column as a Bug attribute, which can be later
used in filters and highlighted in text output.

Usage: cat *.conllu | udapy -HAMX layout=compact ud.ml.MarkFeatsBugs > bugs.html
Windows: python udapy read.Conllu files="a.conllu,b.conllu" merge=1 ud.ml.MarkFeatsBugs write.TextModeTreesHtml files="bugs.html" marked_only=1 layout=compact attributes=form,lemma,upos,xpos,feats,deprel,misc
"""
import udapi.block.ud.markfeatsbugs
import logging
import re

class MarkFeatsBugs(udapi.block.ud.markfeatsbugs.MarkFeatsBugs):

    def process_node(self, node):
        # FOREIGN WORDS ########################################################
        # Do not put any restrictions on words that have Foreign=Yes. These may
        # also have Lang=xx in MISC, which would mean that the official
        # validator would judge them by the rules for language [xx]. But even
        # if they are not fully code-switched (e.g. because they are written in
        # the Malayalam script, like the English verb പ്ലാന്റ് plānṟ "plant"),
        # they still may not have the regular features of Malayalam morphology.
        if node.feats['Foreign'] == 'Yes':
            pass
        # NOUNS AND PROPER NOUNS ###############################################
        elif re.match(r'^(NOUN|PROPN)$', node.upos):
            self.check_required_features(node, ['Animacy', 'Number', 'Case'])
            self.check_allowed_features(node, {
                'Animacy': ['Anim', 'Inan'],
                'Number': ['Sing', 'Plur'],
                'Case': ['Nom', 'Gen', 'Dat', 'Ben', 'Acc', 'Voc', 'Loc', 'Abl', 'Ins', 'Cmp', 'Com', 'All'],
                'Abbr': ['Yes'],
                'Foreign': ['Yes'],
                'Typo': ['Yes']})
        # ADJECTIVES ###########################################################
        elif node.upos == 'ADJ':
            self.check_allowed_features(node, {
                'VerbForm': ['Part'],
                'NumType': ['Ord'],
                'Abbr': ['Yes'],
                'Foreign': ['Yes'],
                'Typo': ['Yes']})
        # PRONOUNS #############################################################
        elif node.upos == 'PRON':
            rf = ['PronType', 'Case']
            af = {
                'PronType': ['Prs', 'Int', 'Ind'], # demonstrative pronouns are treated as third person personal pronouns
                'Case': ['Nom', 'Gen', 'Dat', 'Ben', 'Acc', 'Voc', 'Loc', 'Abl', 'Ins', 'Cmp', 'Com', 'All'],
                'Abbr': ['Yes'],
                'Typo': ['Yes']
            }
            if node.feats['PronType'] == 'Prs':
                af['Reflex'] = ['Yes']
                if node.feats['Reflex'] == 'Yes':
                    rf = ['PronType']
                else: # not reflexive
                    rf.extend(['Person', 'Number'])
                    af['Person'] = ['1', '2', '3']
                    af['Number'] = ['Sing', 'Plur']
                    # 1st and 2nd person do not have gender: ഞാൻ ñān, നീ nī; or 3rd person താൻ tān̕
                    if node.feats['Person'] == '3' and not node.lemma == 'താൻ': # അവൻ avan, അവൾ avaḷ, അത് at, അവർ avaṟ; but not താൻ tān̕
                        rf.append('Deixis')
                        af['Deixis'] = ['Prox', 'Remt']
                        if node.feats['Number'] == 'Sing':
                            rf.append('Gender')
                            af['Gender'] = ['Masc', 'Fem', 'Neut']
                            # third person singular neuter pronouns also distinguish animacy (animate neuter are animals and plants, they have a different accusative form)
                            if node.feats['Gender'] == 'Neut':
                                rf.append('Animacy')
                                af['Animacy'] = ['Anim', 'Inan']
                        else: # plural pronouns do not distinguish gender but they do distinguish animacy
                            rf.append('Animacy')
                            af['Animacy'] = ['Anim', 'Inan']
                    elif node.feats['Person'] == '1' and node.feats['Number'] == 'Plur':
                        rf.append('Clusivity')
                        af['Clusivity'] = ['In', 'Ex']
            # Interrogative pronouns, too, can be case-marked. Therefore, the
            # base form must have Case=Nom.
            # ആര് ār "who" (Nom) എന്ത് ent "what" (Nom, Acc.Inan)
            # ആരെ āre "who" (Acc) എന്തെ ente "what" (Acc.Anim) എന്തിനെ entine "what" (Acc.Anim or maybe Inan but optional)
            # ആരുടെ āruṭe "who" (Gen) എന്തിന് entin "what" (Gen) or "why"
            # ആരൊക്കെ ārokke "who" (Dat?) എന്തൊക്കെ entokke "what" (Dat?)
            #elif node.feats['PronType'] == 'Int':
            #    rf.append('Animacy')
            #    af['Animacy'] = ['Anim', 'Inan']
            self.check_required_features(node, rf)
            self.check_allowed_features(node, af)
        # DETERMINERS ##########################################################
        elif node.upos == 'DET':
            if node.feats['PronType'] == 'Art':
                self.check_required_features(node, ['PronType', 'Definite'])
                self.check_allowed_features(node, {
                    'PronType': ['Art'],
                    'Definite': ['Ind'],
                    'Abbr': ['Yes'],
                    'Typo': ['Yes']
                })
            else:
                self.check_required_features(node, ['PronType'])
                self.check_allowed_features(node, {
                    'PronType': ['Dem', 'Int', 'Rel', 'Ind', 'Neg', 'Tot'],
                    'Deixis': ['Prox', 'Remt'],
                    'Abbr': ['Yes'],
                    'Typo': ['Yes']
                })
        # NUMERALS #############################################################
        elif node.upos == 'NUM':
            self.check_required_features(node, ['NumType', 'NumForm'])
            # Arabic digits and Roman numerals do not have inflection features.
            if re.match(r'^(Digit|Roman)$', node.feats['NumForm']):
                self.check_allowed_features(node, {
                    'NumType': ['Card'],
                    'NumForm': ['Digit', 'Roman'],
                    'Abbr': ['Yes'],
                    'Typo': ['Yes']
                })
            else:
                self.check_required_features(node, ['NumType', 'NumForm', 'Case'])
                self.check_allowed_features(node, {
                    'NumType': ['Card', 'Frac'],
                    'NumForm': ['Word'],
                    'Number': ['Plur'],
                    'Case': ['Nom', 'Gen', 'Dat', 'Ben', 'Acc', 'Voc', 'Loc', 'Abl', 'Ins', 'Cmp', 'Com', 'All'],
                    'Abbr': ['Yes'],
                    'Typo': ['Yes']
                })
        # VERBS ################################################################
        elif node.upos == 'VERB':
            self.check_required_features(node, ['VerbForm'])
            if node.feats['VerbForm'] == 'Inf':
                self.check_allowed_features(node, {
                    'VerbForm': ['Inf'],
                    'Polarity': ['Pos', 'Neg'],
                    'Voice': ['Act', 'Pass', 'Cau'],
                    'Foreign': ['Yes'],
                    'Abbr': ['Yes'],
                    'Typo': ['Yes']
                })
            elif node.feats['VerbForm'] == 'Fin':
                if node.feats['Mood'] == 'Imp':
                    # Unlike other forms, the imperative distinguishes politeness.
                    # The verb stem serves as an informal imperative: തുറ tuṟa "open"
                    # The citation form may serve as a formal imperative: തുറക്കുക tuṟakkūka "open"
                    # Finally, there is another formal imperative with -kkū: തുറക്കൂ tuṟakkū "open"
                    self.check_required_features(node, ['Mood', 'Polite'])
                    self.check_allowed_features(node, {
                        'Aspect': ['Imp', 'Perf', 'Prog'],
                        'VerbForm': ['Fin'],
                        'Mood': ['Imp'],
                        'Polarity': ['Pos', 'Neg'],
                        'Polite': ['Infm', 'Form'],
                        'Abbr': ['Yes'],
                        'Foreign': ['Yes'],
                        'Typo': ['Yes']
                    })
                elif node.feats['Mood'] == 'Nec':
                    self.check_required_features(node, ['Mood', 'Voice'])
                    self.check_allowed_features(node, {
                        'Aspect': ['Imp', 'Perf', 'Prog'],
                        'VerbForm': ['Fin'],
                        'Mood': ['Nec'],
                        'Polarity': ['Pos', 'Neg'],
                        'Voice': ['Act', 'Pass', 'Cau'],
                        'Abbr': ['Yes'],
                        'Foreign': ['Yes'],
                        'Typo': ['Yes']
                    })
                else:
                    self.check_required_features(node, ['Mood', 'Tense', 'Voice'])
                    self.check_allowed_features(node, {
                        'Aspect': ['Imp', 'Perf', 'Prog'],
                        'VerbForm': ['Fin'],
                        'Mood': ['Ind', 'Pot', 'Cnd'],
                        'Tense': ['Past', 'Imp', 'Pres', 'Fut'], # only in indicative
                        'Polarity': ['Pos', 'Neg'],
                        'Voice': ['Act', 'Pass', 'Cau'],
                        'Abbr': ['Yes'],
                        'Foreign': ['Yes'],
                        'Typo': ['Yes']
                    })
            elif node.feats['VerbForm'] == 'Part':
                self.check_required_features(node, ['Tense'])
                self.check_allowed_features(node, {
                    'Aspect': ['Imp', 'Perf', 'Prog'],
                    'VerbForm': ['Part'],
                    'Tense': ['Past'],
                    'Polarity': ['Pos', 'Neg'],
                    'Voice': ['Act', 'Pass', 'Cau'],
                    'Abbr': ['Yes'],
                    'Foreign': ['Yes'],
                    'Typo': ['Yes']
                })
            else: # verbal noun
                # The "actual Malayalam verbal noun" (unlike the "nominalized form") does not inflect for Tense and Voice.
                # Currently both forms are VerbForm=Vnoun.
                #self.check_required_features(node, ['Tense', 'Voice'])
                self.check_allowed_features(node, {
                    'Aspect': ['Imp', 'Perf', 'Prog'],
                    'VerbForm': ['Vnoun'],
                    'Tense': ['Past', 'Pres'],
                    'Gender': ['Masc', 'Fem', 'Neut'],
                    'Polarity': ['Pos', 'Neg'],
                    'Voice': ['Act', 'Pass', 'Cau'],
                    # We only annotate case of verbal nouns if it is not Nom, i.e., there is an actual case suffix.
                    'Case': ['Gen', 'Dat', 'Ben', 'Acc', 'Voc', 'Loc', 'Abl', 'Ins', 'Cmp', 'Com', 'All'],
                    'Abbr': ['Yes'],
                    'Foreign': ['Yes'],
                    'Typo': ['Yes']
                })
        # AUXILIARIES ##########################################################
        elif node.upos == 'AUX':
            self.check_required_features(node, ['VerbForm'])
            if node.feats['VerbForm'] == 'Fin':
                if node.feats['Mood'] == 'Imp':
                    self.check_required_features(node, ['Mood'])
                    self.check_allowed_features(node, {
                        'Aspect': ['Imp', 'Perf', 'Prog'],
                        'VerbForm': ['Fin'],
                        'Mood': ['Imp'],
                        'Polarity': ['Pos', 'Neg'],
                        'Abbr': ['Yes'],
                        'Typo': ['Yes']
                    })
                else: # indicative or subjunctive
                    self.check_required_features(node, ['Mood', 'Tense'])
                    self.check_allowed_features(node, {
                        'Aspect': ['Imp', 'Perf', 'Prog'],
                        'VerbForm': ['Fin'],
                        'Mood': ['Ind', 'Sub', 'Cnd'],
                        'Tense': ['Past', 'Imp', 'Pres', 'Fut'], # only in indicative
                        'Polarity': ['Pos', 'Neg'],
                        'Abbr': ['Yes'],
                        'Typo': ['Yes']
                    })
            else: # verbal noun
                # The "actual Malayalam verbal noun" (unlike the "nominalized form") does not inflect for Tense and Voice.
                # Currently both forms are VerbForm=Vnoun.
                #self.check_required_features(node, ['Tense', 'Voice'])
                self.check_allowed_features(node, {
                    'Aspect': ['Imp', 'Perf', 'Prog'],
                    'VerbForm': ['Vnoun'],
                    'Tense': ['Past', 'Pres'],
                    'Gender': ['Masc', 'Fem', 'Neut'],
                    'Polarity': ['Pos', 'Neg'],
                    # We only annotate case of verbal nouns if it is not Nom, i.e., there is an actual case suffix.
                    'Case': ['Gen', 'Dat', 'Ben', 'Acc', 'Voc', 'Loc', 'Abl', 'Ins', 'Cmp', 'Com', 'All'],
                    'Abbr': ['Yes'],
                    'Typo': ['Yes']
                })
        # ADVERBS ##############################################################
        elif node.upos == 'ADV':
            if node.feats['PronType'] != '':
                # Pronominal adverbs are neither compared nor negated.
                self.check_allowed_features(node, {
                    'PronType': ['Dem', 'Int', 'Rel', 'Ind', 'Neg', 'Tot'],
                    'Typo': ['Yes']
                })
            else:
                # The remaining adverbs are neither pronominal, nor compared or
                # negated.
                self.check_allowed_features(node, {'Typo': ['Yes']})
        # ADPOSITIONS ##########################################################
        elif node.upos == 'ADP':
            self.check_allowed_features(node, {
                # Case suffixes after numbers are separate tokens, they are attached
                # via the 'case' relation and they bear the Case feature (the number does not).
                'Case': ['Gen', 'Dat', 'Ben', 'Acc', 'Voc', 'Loc', 'Abl', 'Ins', 'Cmp', 'Com', 'All'],
                'Abbr': ['Yes'],
                'Typo': ['Yes']})
        # PARTICLES ############################################################
        elif node.upos == 'PART':
            self.check_allowed_features(node, {
                'Polarity': ['Neg'],
                'Abbr': ['Yes'],
                'Typo': ['Yes']
            })
        # THE REST: NO FEATURES ################################################
        else:
            self.check_allowed_features(node, {'Abbr': ['Yes'], 'Typo': ['Yes']})
