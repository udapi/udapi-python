#!/usr/bin/env python3

# Transgressives of Slavic languages

from udapi.core.block import Block
import importlib
import sys

class Slavic_transgressive(Block):
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
		# condition node.upos == 'VERB' to prevent copulas from entering this branch
		if node.feats['VerbForm'] == 'Conv' and node.upos == 'VERB':
			refl = [x for x in node.children if x.feats['Reflex'] == 'Yes']
			neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']
			
			phrase_ords = [node.ord] + [x.ord for x in refl] + [x.ord for x in neg]
			phrase_ords.sort()
			
			self.wr.write_node_info(node,
				person=node.feats['Person'],
				number=node.feats['Number'],
				form='Conv',
				tense=node.feats['Tense'],
				aspect=node.feats['Aspect'],
				polarity=self.wr.get_polarity(node,neg),
				reflex=self.wr.get_is_reflex(node,refl),
				ords=phrase_ords,
				gender=node.feats['Gender'],
				animacy=node.feats['Animacy'],
				voice=self.wr.get_voice(node, refl)
				)

		# passive voice
		elif node.upos == 'ADJ':
			aux = [x for x in node.children if x.udeprel == 'aux' and x.feats['VerbForm'] == 'Conv']
			
			if len(aux) > 0:
				neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']
				auxVerb = aux[0]
				phrase_ords = [node.ord] + [x.ord for x in aux] + [x.ord for x in neg]
				phrase_ords.sort()
			
				self.wr.write_node_info(node,
					person=auxVerb.feats['Person'],
					number=auxVerb.feats['Number'],
					form='Conv',
					tense=auxVerb.feats['Tense'],
					aspect=node.feats['Aspect'],
					polarity=self.wr.get_polarity(auxVerb,neg),
					ords=phrase_ords,
					gender=auxVerb.feats['Gender'],
					animacy=auxVerb.feats['Animacy'],
					voice='Pass'
				)

		# copulas
		else:
			cop = [x for x in node.children if x.udeprel == 'cop' and x.feats['VerbForm'] == 'Conv']
			
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
					tense=copVerb.feats['Tense'],
					gender=copVerb.feats['Gender'],
					animacy=copVerb.feats['Animacy'],
					form='Conv',
					polarity=self.wr.get_polarity(node,neg),
					ords=phrase_ords,
					voice=self.wr.get_voice(node, refl)
					)

