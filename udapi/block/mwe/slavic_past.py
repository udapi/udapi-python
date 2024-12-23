#!/usr/bin/env python3

# Past tense of Slavic languages

from udapi.core.block import Block
import importlib
import sys

class Slavic_past(Block):
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

	def get_person_for_langs_with_simple_past(self, node, person):
		"""
		returns the person which is known from subject, languages with the simple past tense (e. g. Russian) do not express person in these verb forms
		if the person was not taken from the subject, the third person would be filled in automatically due to languages ​​with a compound past but simple forms for the third person  (e. g. Czech)
		"""
		subj = [x for x in node.children if x.udeprel == "nsubj"]
		if subj:
			subj = subj[0]
			if subj.feats['Person'] != '':
				person = subj.feats['Person']
		return person

	def process_node(self, node):

		cop = [x for x in node.children if x.udeprel == "cop" and x.feats['Tense'] == 'Past']

		# compound past tense
		if node.feats['VerbForm'] == 'Part' and node.upos == 'VERB' and node.feats['Voice'] != 'Pass':
			aux = [x for x in node.children if x.udeprel == 'aux' and x.feats['Tense'] == 'Pres']
			refl = [x for x in node.children if x.feats['Reflex'] == 'Yes']
			neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']
			
			phrase_ords = [node.ord] + [x.ord for x in aux] + [x.ord for x in refl] + [x.ord for x in neg]
			phrase_ords.sort()
			
			aux_cnd = [x for x in node.children if x.feats['Mood'] == 'Cnd' or x.deprel == 'aux:cnd'] # we don't want to mark l-participles in the conditional as past tense
			if len(aux_cnd) == 0:
				if len(aux) > 0:
					person = aux[0].feats['Person']

				elif len(aux) == 0:
					person = '3'


				self.wr.write_node_info(node,
						tense='Past',
						person=person,
						number=node.feats['Number'],
						mood='Ind',
						voice=self.wr.get_voice(node,refl),
						aspect=node.feats['Aspect'],
						form='Fin',
						polarity=self.wr.get_polarity(node,neg),
						reflex=self.wr.get_is_reflex(node,refl),
						ords=phrase_ords,
						gender=node.feats['Gender'],
						animacy=node.feats['Animacy']
						)

		# the past tense of some Slavic languages ​​is formed only by a verb without an auxiliary verb (e.g. Polish)
		elif node.feats['Tense'] == 'Past' and node.upos == 'VERB' and node.feats['VerbForm'] != 'Conv':
			refl = [x for x in node.children if x.feats['Reflex'] == 'Yes']
			neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']
			
			phrase_ords = [node.ord] + [x.ord for x in refl] + [x.ord for x in neg]
			phrase_ords.sort()

			self.wr.write_node_info(node,
				tense='Past',
				person=node.feats['Person'],
				number=node.feats['Number'],
				mood='Ind',
				voice=self.wr.get_voice(node,refl),
				aspect=node.feats['Aspect'],
				form=node.feats['VerbForm'],
				polarity=self.wr.get_polarity(node,neg),
				reflex=self.wr.get_is_reflex(node,refl),
				ords=phrase_ords,
				gender=node.feats['Gender'],
				animacy=node.feats['Animacy']
				)
			
			
		# passivum
		elif node.upos == 'ADJ' and node.feats['Voice'] == 'Pass' and len(cop) == 0:	
			aux_past_tense = [x for x in node.children if x.udeprel == 'aux' and x.feats['Tense'] == 'Past']
			aux_cnd = [x for x in node.children if x.feats['Mood'] == 'Cnd' or x.deprel == 'aux:cnd'] # we don't want to mark l-participles in the conditional as past tense
			if len(aux_cnd) == 0:
				if len(aux_past_tense) > 0:
					aux_pres_tense = [x for x in  node.children if x.udeprel == 'aux' and x.feats['Tense'] == 'Pres'] # e. g. the auxiliary 'jsem' in the phrase 'byl jsem přinucen'
					neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']
					phrase_ords = [node.ord] + [x.ord for x in aux_past_tense] + [x.ord for x in aux_pres_tense] + [x.ord for x in neg]
					phrase_ords.sort()
					
					person = '3'
					if aux_pres_tense:
						person = aux_pres_tense[0].feats['Person']
					person = self.get_person_for_langs_with_simple_past(node, person)

					self.wr.write_node_info(node,
						tense='Past',
						person=person,
						number=aux_past_tense[0].feats['Number'],
						mood='Ind',
						voice='Pass',
						form='Fin',
						aspect=node.feats['Aspect'],
						polarity=self.wr.get_polarity(aux_past_tense[0],neg),
						ords=phrase_ords,
						gender=node.feats['Gender'],
						animacy=node.feats['Animacy']
						)
				
		else:
			aux_cnd = [x for x in node.children if x.feats['Mood'] == 'Cnd' or x.deprel == 'aux:cnd'] # we don't want to mark l-participles in the conditional as past tense
			if len(cop) > 0 and len(aux_cnd) == 0:
				aux_past_tense = [x for x in node.children if x.udeprel == 'aux' and x.feats['Tense'] == 'Pres']
				prep = [x for x in node.children if x.upos == 'ADP']
				neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']
				refl = [x for x in node.children if x.feats['Reflex'] == 'Yes']

				phrase_ords = [node.ord] + [x.ord for x in aux_past_tense] + [x.ord for x in cop] + [x.ord for x in prep] + [x.ord for x in neg] + [x.ord for x in refl]
				phrase_ords.sort()

				person = '3'
				if aux_past_tense:
					person = aux_past_tense[0].feats["Person"]
				person = self.get_person_for_langs_with_simple_past(node, person)
				
				self.wr.write_node_info(node,
					tense='Past',
					person=person,
					number=cop[0].feats['Number'],
					mood='Ind',
					voice=self.wr.get_voice(node, refl),
					form='Fin',
					reflex=self.wr.get_is_reflex(node,refl),
					polarity=self.wr.get_polarity(cop[0],neg),
					ords=phrase_ords,
					gender=cop[0].feats['Gender'],
					animacy=cop[0].feats['Animacy']
					)
