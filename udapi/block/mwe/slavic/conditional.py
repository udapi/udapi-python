#!/usr/bin/env python3

# Conditional mood of Slavic languages

from udapi.core.block import Block
import importlib
import sys

class Slavic_cond(Block):
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
		if node.feats['VerbForm'] == 'Part' or node.feats['VerbForm'] == 'Fin':
			# in most Slavic languages, the verb has feats['VerbForm'] == 'Part' but in Polish the verb has feats['VerbForm'] == 'Fin'
			
			aux_cnd = [x for x in node.children if x.feats['Mood'] == 'Cnd' or x.deprel == 'aux:cnd'] # list for auxiliary verbs for forming the conditional mood
			cop = [x for x in node.children if x.udeprel == 'cop'] # in some cases it may happen that the cop follows the noun, we don't want to these cases in this branch
			# in Polish the auxiliary verbs for conditional mood have deprel == 'aux:cnd', in other languages the auxiliary verbs have x.feats['Mood'] == 'Cnd'
			
			# the conditional mood can be formed using the auxiliary verb or some conjunctions (such as 'aby, kdyby...' in Czech)
			# so x.udeprel == 'aux' can't be required because it doesn't meet the conjunctions
			
			if len(aux_cnd) > 0 and len(cop) == 0:
				aux = [x for x in node.children if x.udeprel == 'aux' or x.feats['Mood'] == 'Cnd'] # all auxiliary verbs and conjuctions with feats['Mood'] == 'Cnd'
				refl = [x for x in node.children if x.feats['Reflex'] == 'Yes']
				neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']
				
				phrase_ords = [node.ord] + [x.ord for x in aux] + [x.ord for x in refl] + [x.ord for x in neg]
				phrase_ords.sort()
			
				auxVerb = aux_cnd[0]

				person='3' # TODO there could be a problem in russian etc. (same as in past tense)
				if auxVerb.feats['Person'] != '':
					person=auxVerb.feats['Person']
				
					
				self.wr.write_node_info(node,
					person=person,
					number=node.feats['Number'],
					mood='Cnd',
					form='Fin',
					aspect=node.feats['Aspect'],
					reflex=self.wr.get_is_reflex(node,refl),
					polarity=self.wr.get_polarity(node,neg),
					voice=self.wr.get_voice(node, refl),
					ords=phrase_ords,
					gender=node.feats['Gender'],
					animacy=node.feats['Animacy']
				)
				return
		
					
		cop = [x for x in node.children if x.udeprel == 'cop' and (x.feats['VerbForm'] == 'Part' or x.feats['VerbForm'] == 'Fin')]
		aux_cnd = [x for x in node.children if x.feats['Mood'] == 'Cnd' or x.deprel=='aux:pass']
			
		if len(cop) > 0 and len(aux_cnd) > 0:
			aux = [x for x in node.children if x.udeprel == 'aux' or x.feats['Mood'] == 'Cnd']
			neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']
			prep = [x for x in node.children if x.upos == 'ADP']
			refl = [x for x in node.children if x.feats['Reflex'] == 'Yes']

			copVerb = cop[0]
			phrase_ords = [node.ord] + [x.ord for x in aux] + [x.ord for x in cop] + [x.ord for x in neg] + [x.ord for x in prep] + [x.ord for x in refl]
			phrase_ords.sort()
			self.wr.write_node_info(node,
					person=copVerb.feats['Person'],
					number=copVerb.feats['Number'],
					mood='Cnd',
					form='Fin',
					voice=self.wr.get_voice(node, refl),
					polarity=self.wr.get_polarity(copVerb,neg),
					reflex=self.wr.get_is_reflex(node, refl),
					ords=phrase_ords,
					gender=copVerb.feats['Gender'],
					animacy=copVerb.feats['Animacy']
			)
				
