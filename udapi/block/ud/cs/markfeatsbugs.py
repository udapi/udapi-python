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
                if node.feats['Gender'] == 'Masc':
                    self.check_required_features(node, ['VerbForm', 'Aspect', 'Voice', 'Gender', 'Animacy', 'Number', 'Case', 'Polarity'])
                    self.check_allowed_features(node, {
                        'VerbForm': ['Part'],
                        'Aspect': ['Imp', 'Perf'],
                        'Voice': ['Act', 'Pass'],
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
                        'Voice': ['Act', 'Pass'],
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
