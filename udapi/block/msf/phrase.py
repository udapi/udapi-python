"""
Morphosyntactic features (UniDive):
An abstract block as a base for derivation of blocks that discover periphrastic
verb forms and save them as Phrase features in MISC. This block provides the
methods that save the features in MISC. It is based on the Writer module by
Lenka Krippnerová.
"""
from udapi.core.block import Block
import logging

class Phrase(Block):

    def __init__(self, feature_prefix='CG', **kwargs):
        """
        Parameters:
        feature_prefix (string) - The prefix of phrase features (e. g. 'CG', 'Phrase'), default is 'CG'
        """
        super().__init__(**kwargs)
        self.feature_prefix = feature_prefix

        self.dictionary = {
            'person': f'{feature_prefix}Person',
            'number': f'{feature_prefix}Number',
            'mood': f'{feature_prefix}Mood',
            'tense': f'{feature_prefix}Tense',
            'voice': f'{feature_prefix}Voice',
            'aspect':f'{feature_prefix}Aspect',
            'form': f'{feature_prefix}Form',
            'reflex': f'{feature_prefix}Reflex',
            'polarity': f'{feature_prefix}Polarity',
            'gender': f'{feature_prefix}Gender',
            'animacy': f'{feature_prefix}Animacy',
            'ords': feature_prefix,
            'expl': f'{feature_prefix}Expl',
            'analytic': 'Analytic',
            }
        
        # a dictionary where the key is the lemma of a negative particle and the value is a list of the lemmas of their possible children that have a 'fixed' relation
        # we do not want to include these negative particles in the phrase; these are expressions like "never", etc.
        self.negation_fixed = {
            # Belarusian
            'ні' : ['раз'],
            'ня' : ['толькі'],

            # Upper Sorbian
            'nic' : ['naposledku'],

            # Polish
            'nie' : ['mało'],

            # Pomak
            'néma' : ['kak'],

            # Slovenian
            'ne' : ['le'],

            # Russian and Old East Slavic
            'не' : ['то', 'токмо'],
            'ни' : ['в', 'раз', 'шатко'],
            'нет' : ['нет']
        }

    def process_node(self, node):
        """
        Override this in a derived class!
        """
        logging.fatal('process_node() not implemented.')

    

    def write_node_info(self, node,
			tense = None,
			person = None,
			number = None,
			mood = None,
			voice = None,
			form = None,
			reflex = None,
			polarity = None,
			ords = None,
			gender = None,
			animacy = None,
			aspect = None,
            expl=None,
            analytic=None):
        arguments = locals()
        del arguments['self'] # delete self and node from arguments,
        del arguments['node'] # we want only grammatical categories 
        for key,val in arguments.items():
            if val != None: 
                node.misc[self.dictionary[key]] = val

    def has_fixed_children(self, node):
        """
        Returns True if the node has any children with the 'fixed' relation and the node's lemma along with the child's lemma are listed in self.negation_fixed.
        """
        fixed_children = [x for x in node.children if x.udeprel == 'fixed']

        if fixed_children:
            if fixed_children[0].lemma in self.negation_fixed.get(node.lemma, []):
                return True
        return False

    def get_polarity(self, nodes):
        """
        Returns 'Neg' if there is exactly one node with Polarity='Neg' among the given nodes.
        Returns an empty string if there are zero or more than one such nodes.
        """
        neg_count = 0
        for node in nodes:
            if node.feats['Polarity'] == 'Neg':
                neg_count += 1

        if neg_count == 1:
            return 'Neg'
        
        # neg_count can be zero or two, in either case we want to return an empty string so that the PhrasePolarity attribute is not generated
        else:
            return ''
               
    def get_negative_particles(self, nodes):
        """
        Returns a list of all negative particles found among the children 
        of the specified nodes, except for negative particles with fixed children specified in self.negation_fixed.
        """
        neg_particles = []
        for node in nodes:
            neg = [x for x in node.children if x.upos == 'PART' and x.feats['Polarity'] == 'Neg' and x.udeprel == 'advmod' and not self.has_fixed_children(x)]
            if neg:
                neg_particles += neg
        return neg_particles
            
		
    def get_is_reflex(self,node,refl):
        if node.feats['Voice'] == 'Mid':
            return 'Yes'
        if len(refl) == 0:
            return node.feats['Reflex']
        return 'Yes'
    
    def get_expl_type(self,node, refl):
        if node.feats['Voice'] == 'Mid':
            return 'Pv'
        if not refl:
            return ''
        if refl[0].deprel == 'expl':
            return 'Pv'
        return refl[0].deprel.split(':')[1].capitalize()

    def is_expl_pass(self,refl):
        if len(refl) == 0:
            return False
        return refl[0].deprel == 'expl:pass'
		
    def get_voice(self,node,refl):
        voice = node.feats['Voice']
        if self.is_expl_pass(refl):
            return 'Pass'
        return voice
    
    def get_analytic_bool(self,node):
        auxes = [x for x in node.children if x.udeprel == 'aux']

        if auxes:
            return 'Yes'
        else:
            return 'No'

