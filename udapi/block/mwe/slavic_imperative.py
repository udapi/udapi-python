#!/usr/bin/env python3

# Imperative of Slavic languages

from udapi.core.block import Block
import importlib
import sys

class Slavic_imperative(Block):
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
	
	def process_node(self, node):
		# the condition node.upos == 'VERB' ensures that copulas do not enter this branch
		if node.feats['Mood'] == 'Imp' and node.upos == 'VERB':
			refl = [x for x in node.children if x.feats['Reflex'] == 'Yes']
			neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']
			
			phrase_ords = [node.ord] + [x.ord for x in refl] + [x.ord for x in neg]
			phrase_ords.sort()
			
			self.wr.write_node_info(node,
				person=node.feats['Person'],
				number=node.feats['Number'],
				aspect=node.feats['Aspect'],
				mood='Imp',
				form='Fin',
				voice='Act',
				polarity=self.wr.get_polarity(node,neg),
				reflex=self.wr.get_is_reflex(node,refl),
				ords=phrase_ords
				)
			return
			
		# verbs in the passive forms are marked as ADJ
		if node.upos == 'ADJ' and node.feats['Voice'] == 'Pass':
			aux = [x for x in node.children if x.udeprel == 'aux' and x.feats['Mood'] == 'Imp']
			if len(aux) > 0:
				neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']
				
				phrase_ords = [node.ord] + [x.ord for x in aux] + [x.ord for x in neg]
				phrase_ords.sort()
				
				self.wr.write_node_info(node,
					person=aux[0].feats['Person'],
					number=aux[0].feats['Number'],
					mood='Imp',
					voice='Pass',
					aspect=node.feats['Aspect'],
					form='Fin',
					polarity=self.wr.get_polarity(node,neg),
					ords=phrase_ords,
					gender=node.feats['Gender'],
					animacy=node.feats['Animacy']
					)
				return


		cop = [x for x in node.children if x.udeprel == 'cop' and x.feats['Mood'] == 'Imp']
		if len(cop) > 0:
			prep = [x for x in node.children if x.upos == 'ADP']
			neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']
			refl = [x for x in node.children if x.feats['Reflex'] == 'Yes']

			copVerb = cop[0]
			phrase_ords = [node.ord] + [x.ord for x in cop] + [x.ord for x in prep] + [x.ord for x in neg] + [x.ord for x in refl]
			phrase_ords.sort()
				
			self.wr.write_node_info(node,
				person=copVerb.feats['Person'],
				number=copVerb.feats['Number'],
				mood='Imp',
				form='Fin',
				voice=self.wr.get_voice(node, refl),
				reflex=self.wr.get_is_reflex(node, refl),
				polarity=self.wr.get_polarity(node,neg),
				ords=phrase_ords
				)
				


