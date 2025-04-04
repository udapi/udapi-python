#!/usr/bin/env python3

# Infinitive of Slavic languages

from udapi.core.block import Block
import importlib
import sys

class Slavic_inf(Block):
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
		if node.feats['VerbForm'] == 'Inf' and node.upos == 'VERB':
			aux = [x for x in node.children if x.udeprel == 'aux']
			if len(aux) == 0: # the list of auxiliary list must be empty - we don't want to mark infinitives which are part of any other phrase (for example the infinititive is part of the future tense in Czech)
				refl = [x for x in node.children if x.feats['Reflex'] == 'Yes']
				neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']
				
				phrase_ords = [node.ord] + [x.ord for x in refl] + [x.ord for x in neg]
				phrase_ords.sort()
				
				voice='Act'
				if self.wr.is_expl_pass(refl):
					voice='Pass'
				
				self.wr.write_node_info(node,
					aspect=node.feats['Aspect'],
					voice=voice,
					form='Inf',
					polarity=self.wr.get_polarity(node,neg),
					reflex=self.wr.get_is_reflex(node,refl),
					ords=phrase_ords
				)
				return
		
		if node.upos == 'ADJ' and node.feats['Voice'] == 'Pass':
			aux = [x for x in node.children if x.udeprel == 'aux' and x.feats['VerbForm'] == 'Inf']
			aux_forb = [x for x in node.children if x.udeprel == 'aux' and x.feats['VerbForm'] != 'Inf']
			if len(aux) > 0 and len(aux_forb) == 0:
				neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']
				refl = [x for x in node.children if x.feats['Reflex'] == 'Yes']

				phrase_ords = [node.ord] + [x.ord for x in aux] + [x.ord for x in neg] + [x.ord for x in refl]
				phrase_ords.sort()
				
				self.wr.write_node_info(node,
					aspect=node.feats['Aspect'],
					voice='Pass',
					form='Inf',
					polarity=self.wr.get_polarity(aux[0],neg),
					reflex=self.wr.get_is_reflex(node, refl),
					ords=phrase_ords,
					gender=node.feats['Gender'],
					animacy=node.feats['Animacy'],
					number=node.feats['Number']
					)
				return
					
		

		cop = [x for x in node.children if x.udeprel == 'cop' and x.feats['VerbForm'] == 'Inf']
		aux_forb = [x for x in node.children if x.udeprel == 'aux']
		if len(cop) > 0 and len(aux_forb) == 0:
			prep = [x for x in node.children if x.upos == 'ADP']
			neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']
			refl = [x for x in node.children if x.feats['Reflex'] == 'Yes']
			phrase_ords = [node.ord] + [x.ord for x in cop] + [x.ord for x in prep] + [x.ord for x in neg] + [x.ord for x in refl]
			phrase_ords.sort()
			
			self.wr.write_node_info(node,
				voice=self.wr.get_voice(node, refl),
				form='Inf',
				polarity=self.wr.get_polarity(cop[0],neg),
				reflex=self.wr.get_is_reflex(node, refl),
				ords=phrase_ords
				)
							
