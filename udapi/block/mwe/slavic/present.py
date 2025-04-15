#!/usr/bin/env python3

# Present tense of Slavic languages

from udapi.core.block import Block
import importlib
import sys

class Slavic_pres(Block):
	def __init__(self, writer_prefix='',**kwargs):
		super().__init__(**kwargs)
		if writer_prefix != '':
			writer_module = ".".join([writer_prefix,'writer'])
		else:
			writer_module = 'writer'
		try:
			module = importlib.import_module(writer_module)
		except ModuleNotFoundError as e:
			print(e, file=sys.stderr)
			print("Try to set writer_prefix parameter.", file=sys.stderr)
			exit(1)

		self.wr = module.Writer()
		
	def process_node(self,node):
		# the condition VerbForm == 'Fin' ensures that there are no transgressives between the found verbs
		
		if node.feats['Tense'] == 'Pres' and node.upos == 'VERB' and node.feats['VerbForm'] == 'Fin': #and node.feats['Aspect']=='Imp':
			refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']
			neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']
			aux_forb = [x for x in node.children if x.upos == 'AUX' and (x.lemma == 'ќе' or x.lemma == 'ще' or x.feats['Mood'] == 'Cnd')] # forbidden auxiliaries for present tense (these auxiliaries are used for the future tense or the conditional mood)

			if len(aux_forb) == 0:
				phrase_ords = [node.ord] + [x.ord for x in refl] + [x.ord for x in neg]
				phrase_ords.sort()
				
				self.wr.write_node_info(node,
					tense='Pres',
					person=node.feats['Person'],
					number=node.feats['Number'],
					mood='Ind',
					aspect=node.feats['Aspect'],
					voice=self.wr.get_voice(node,refl),
					form='Fin',
					polarity=self.wr.get_polarity(node,neg),
					reflex=self.wr.get_is_reflex(node,refl),
					ords=phrase_ords
					)
				return
				

		# passive voice
		if node.upos == 'ADJ' and node.feats['Voice'] == 'Pass':
			aux = [x for x in node.children if x.udeprel == 'aux' and x.feats['Tense'] == 'Pres' and x.lemma != 'hteti' and x.lemma != 'htjeti']
			aux_forb = [x for x in node.children if x.udeprel == 'aux' and x.feats['Tense'] != 'Pres'] # we don't want the past passive (e. g. 'byl jsem poučen' in Czech)
			neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']
			
			phrase_ords = [node.ord] + [x.ord for x in aux] + [x.ord for x in neg]
			phrase_ords.sort()
			
			if len(aux) > 0 and len(aux_forb) == 0:
				auxVerb = aux[0]

				self.wr.write_node_info(node,
					tense='Pres',
					person=auxVerb.feats['Person'],
					number=auxVerb.feats['Number'],
					mood='Ind',
					aspect=node.feats['Aspect'],
					form='Fin',
					voice='Pass',
					polarity=self.wr.get_polarity(auxVerb,neg),
					ords=phrase_ords,
					gender=node.feats['Gender'],
					animacy=node.feats['Animacy']
					)
				return

		cop = [x for x in node.children if x.udeprel == "cop" and x.feats['Tense'] == "Pres"]
		aux = [x for x in node.children if x.udeprel == "aux" and x.feats['Mood'] == "Ind" and x.feats['Tense'] == 'Pres']
		aux_forb = [x for x in node.children if x.upos == 'AUX' and x.feats['Tense'] != 'Pres'] # in Serbian this can be a future tense
		prep = [x for x in node.children if x.upos == 'ADP']
		neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']
		refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']
			
		if len(cop) > 0 and len(aux_forb) == 0:
			copVerb = cop[0]
				
			phrase_ords = [node.ord] + [x.ord for x in cop] + [x.ord for x in aux] + [x.ord for x in prep] + [x.ord for x in neg] + [x.ord for x in refl]
			phrase_ords.sort()
				
			self.wr.write_node_info(node,
					tense='Pres',
					person=copVerb.feats['Person'],
					number=copVerb.feats['Number'],
					aspect=node.feats['Aspect'],
					mood='Ind',
					form='Fin',
					voice=self.wr.get_voice(copVerb, refl),
					reflex=self.wr.get_is_reflex(node, refl),
					polarity=self.wr.get_polarity(copVerb,neg),
					ords=phrase_ords
				)

