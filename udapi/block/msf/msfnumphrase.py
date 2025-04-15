"""
Morphosyntactic features (UniDive):
Case in Number Phrases like 'pět mužů' (five men) in Czech.
"""
from udapi.core.block import Block

class MsfNumPhrase(Block):


    def process_node(self, node):
        """
        Nouns with a 'nummod:gov' dependent are morphologically in genitive,
        but the case of the whole phrase (number + counted noun) is different,
        probably nominative or accusative.
        """
        quantifiers = [x for x in node.children if x.deprel in ['nummod:gov', 'det:numgov']]
        current_case = node.misc['MSFCase']
        if (current_case == 'Gen' or current_case == '') and quantifiers:
            quantifier_case = quantifiers[0].misc['MSFCase']
            # The quantifier may lack the case feature (e.g. numbers expressed by digits)
            # but we may be able to guess it from a preposition or other factors.
            if quantifier_case == '':
                # Not any 'case' dependent is helpful. Here we really need single-word
                # adposition.
                adpositions = [x for x in node.children if x.udeprel == 'case' and x.upos == 'ADP']
                if len(adpositions) == 1:
                    fixed = [x for x in adpositions[0].children if x.udeprel == 'fixed']
                    if not fixed and adpositions[0].feats['Case']:
                        quantifier_case = adpositions[0].feats['Case']
            # Finally, if the above did not help, we may guess the case from the deprel of the node itself.
            if quantifier_case == '':
                if node.udeprel == 'nsubj':
                    quantifier_case = 'Nom'
                elif node.udeprel == 'obj':
                    quantifier_case = 'Acc'
            node.misc['MSFCase'] = quantifier_case
