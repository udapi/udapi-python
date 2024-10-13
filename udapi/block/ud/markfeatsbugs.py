"""
Block to identify missing or ill-valued features in a treebank. Any bugs that it
finds will be saved in the MISC column as a Bug attribute, which can be later
used in filters and highlighted in text output. This is a base block that only
implements service methods. A language-specific block must be derived from this
one and define the actual rules valid in that language.

Usage (Czech example): cat *.conllu | udapy -HAMX layout=compact ud.cs.MarkFeatsBugs > bugs.html
"""
from udapi.core.block import Block

class MarkFeatsBugs(Block):

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
        """
        This is a generic block, do nothing here. In a language-specific block
        based on this one, rules similar to the examples below can be specified:

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
        #...
        # THE REST: NO FEATURES ################################################
        else:
            self.check_allowed_features(node, {})
        """
        return
