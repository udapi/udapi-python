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

    def process_node(self, node):
        """
        Override this in a derived class!
        """
        logging.fatal('process_node() not implemented.')

    dictionary = {
		'person': 'PhrasePerson',
		'number': 'PhraseNumber',
		'mood': 'PhraseMood',
		'tense': 'PhraseTense',
		'voice': 'PhraseVoice',
		'aspect':'PhraseAspect',
		'form': 'PhraseForm',
		'reflex': 'PhraseReflex',
		'polarity': 'PhrasePolarity',
		'gender':'PhraseGender',
		'animacy':'PhraseAnimacy',
		'ords':'Phrase'
		}

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
			aspect = None):
        arguments = locals()
        del arguments['self'] # delete self and node from arguments,
        del arguments['node'] # we want only grammatical categories 
        for key,val in arguments.items():
            if val != None: 
                node.misc[self.dictionary[key]] = val

    def get_polarity(self, node, neg):
        if node.feats['Polarity'] != "":
            return node.feats['Polarity']
        if len(neg) == 0:
            return None
        return 'Neg'
		
    def get_is_reflex(self,node,refl):
        if len(refl) == 0:
            return node.feats['Reflex']
        return 'Yes'

    def is_expl_pass(self,refl):
        if len(refl) == 0:
            return False
        return refl[0].deprel == 'expl:pass'
		
    def get_voice(self,node,refl):
        voice = node.feats['Voice']
        if self.is_expl_pass(refl):
            return 'Pass'
        return voice
		
