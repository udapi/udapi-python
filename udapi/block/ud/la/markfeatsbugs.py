"""
Block to identify missing or ill-valued features in Latin. Any bugs that it
finds will be saved in the MISC column as a Bug attribute, which can be later
used in filters and highlighted in text output.

Usage: cat *.conllu | udapy -HAM ud.la.MarkFeatsBugs > bugs.html
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
