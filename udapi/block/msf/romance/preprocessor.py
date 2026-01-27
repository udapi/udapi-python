from phrase import Phrase
from enum import Enum

class Preprocessor(Phrase):


    def process_node(self, node):

        # In Porttinari treebank, the negative adverb não is not marked with feat Polarity=Neg
        if node.lemma == 'não' and node.upos == 'ADV':
            node.feats['Polarity'] = 'Neg'

        if node.upos == 'ADV' and node.feats['PronType'] == 'Neg':
            node.feats['PronType'] = ''
            node.feats['Polarity'] = 'Neg'

        # In Romanian RRT treebank, there is no annotation of the voice feature
        # Automatically assign passive voice
        pass_auxes = [x for x in node.children if x.deprel == 'aux:pass']
        if pass_auxes:
            node.feats['Voice'] = 'Pass'