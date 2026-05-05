"""
Block ud.gl.Prep tries to solve some errors in Galician CTG where
a preposition is mistakenly attached as a sibling of its noun.

Author: Dan Zeman
"""
from udapi.core.block import Block

class Prep(Block):
    """Block for fixing prepositions in UD_Galician-CTG."""

    def process_node(self, node):
        if node.upos == 'ADP' and node.parent.ord < node.ord:
            rightsiblings = node.siblings(following_only=True)
            if len(rightsiblings) > 0 and rightsiblings[0].upos in ['NOUN', 'PROPN', 'PRON']:
                noun = rightsiblings[0]
                if noun.is_descendant_of(node):
                    noun.parent = node.parent
                noun.deprel = 'obl' if noun.parent.upos in ['VERB', 'ADJ', 'ADV'] else 'nmod'
                node.parent = noun
                node.deprel = 'case'
                for x in node.children:
                    x.parent = noun
