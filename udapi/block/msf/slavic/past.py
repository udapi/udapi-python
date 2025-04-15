"""
Morphosyntactic features (UniDive, Lenka Krippnerová):
This block detects past tense forms in Slavic languages and saves their
features as Phrase* attributes in MISC of their head word.
"""

import udapi.block.msf.msfphrase

class Past(udapi.block.msf.msfphrase.MsfPhrase):

	def get_person_for_langs_with_simple_past(self, node, person):
		"""
		returns the person which is known from subject, languages with the simple past tense (e. g. Russian) do not express person in these verb forms
		if the person was not taken from the subject, the third person would be filled in automatically due to languages ​​with a compound past but simple forms for the third person  (e. g. Czech)
		"""
		subj = [x for x in node.children if x.udeprel == 'nsubj']
		if subj:
			subj = subj[0]
			if subj.feats['Person'] != '':
				person = subj.feats['Person']
		return person

	def process_node(self, node):
		
		past_tenses = ['Past', 'Imp', 'Pqp']
		cop = [x for x in node.children if x.udeprel == 'cop' and (x.feats['Tense'] in past_tenses)]

		# there is person 0 in Polish and Ukrainian which is for impersonal statements
		# in Polish, verbs with Person=0 have also Tense=Past, in Ukrainian the tense is not specified
		if node.feats['Person'] == '0':
			refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']
			neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']

			phrase_ords = [node.ord] + [x.ord for x in refl] + [x.ord for x in neg]
			phrase_ords.sort()

			self.write_node_info(node,
						tense=node.feats['Tense'],
						person=node.feats['Person'],
						number=node.feats['Number'],
						mood=node.feats['Mood'],
						voice='Pass',
						aspect=node.feats['Aspect'],
						form=node.feats['VerbForm'],
						polarity=self.get_polarity(node,neg),
						reflex=self.get_is_reflex(node,refl),
						ords=phrase_ords,
						gender=node.feats['Gender'],
						animacy=node.feats['Animacy']
						)

		# compound past tense
		if (node.feats['VerbForm'] == 'Part' or node.feats['VerbForm'] == 'PartRes') and node.upos == 'VERB' and node.feats['Voice'] != 'Pass':
			aux = [x for x in node.children if x.udeprel == 'aux' and x.feats['Tense'] == 'Pres']
			aux_pqp = [x for x in node.children if x.udeprel == 'aux' and x.feats['Tense'] in past_tenses]
			refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']
			neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']
			
			phrase_ords = [node.ord] + [x.ord for x in aux] + [x.ord for x in refl] + [x.ord for x in neg] + [x.ord for x in aux_pqp]
			phrase_ords.sort()
			
			aux_cnd = [x for x in node.children if (x.feats['Mood'] == 'Cnd' or x.deprel == 'aux:cnd') and x.udeprel != 'conj'] # we don't want to mark l-participles in the conditional as past tense
			if len(aux_cnd) == 0:
				if len(aux) > 0:
					person = aux[0].feats['Person']

				elif len(aux) == 0:
					person = '3'

				if len(aux_pqp) > 0:
					person = aux_pqp[0].feats['Person']
				
				# in Slovenian, the participles are not annotated as Tense='Past', the Tense feature is missing here
				# but in Bulgarian, there are cases where the participles are annotated as Tense='Imp'
				tense = 'Past'
				if node.feats['Tense'] == 'Imp':
					tense = 'Imp'
				if node.feats['Tense'] == 'Pqp':
					tense = 'Pqp'

				self.write_node_info(node,
						tense=tense,
						person=person,
						number=node.feats['Number'],
						mood='Ind',
						voice=self.get_voice(node,refl),
						aspect=node.feats['Aspect'],
						form='Fin',
						polarity=self.get_polarity(node,neg),
						reflex=self.get_is_reflex(node,refl),
						ords=phrase_ords,
						gender=node.feats['Gender'],
						animacy=node.feats['Animacy']
						)
				

		# the past tense of some Slavic languages ​​is formed only by a verb without an auxiliary verb (e.g. Polish)
		# or imperfect (special case of the past tense) e.g. in Bulgarian or Croatian 
		elif (node.feats['Tense'] in past_tenses) and node.upos == 'VERB' and node.feats['VerbForm'] != 'Conv':

			# the past tense is formed only by a content verb, not with an auxiliary
			aux_forb = [x for x in node.children if x.udeprel == 'aux']

			refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']
			neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']

			if not aux_forb:
			
				phrase_ords = [node.ord] + [x.ord for x in refl] + [x.ord for x in neg]
				phrase_ords.sort()

				self.write_node_info(node,
					tense=node.feats['Tense'],
					person=node.feats['Person'],
					number=node.feats['Number'],
					mood='Ind',
					voice=self.get_voice(node,refl),
					aspect=node.feats['Aspect'],
					form=node.feats['VerbForm'],
					polarity=self.get_polarity(node,neg),
					reflex=self.get_is_reflex(node,refl),
					ords=phrase_ords,
					gender=node.feats['Gender'],
					animacy=node.feats['Animacy']
					)
			
				
			
		# passive
		elif node.upos == 'ADJ' and node.feats['Voice'] == 'Pass' and len(cop) == 0:	
			aux_past_tense = [x for x in node.children if x.udeprel == 'aux' and (x.feats['Tense'] in past_tenses)]
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

					self.write_node_info(node,
						tense=aux_past_tense[0].feats['Tense'],
						person=person,
						number=aux_past_tense[0].feats['Number'],
						mood='Ind',
						voice='Pass',
						form='Fin',
						aspect=node.feats['Aspect'],
						polarity=self.get_polarity(aux_past_tense[0],neg),
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
				refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']

				phrase_ords = [node.ord] + [x.ord for x in aux_past_tense] + [x.ord for x in cop] + [x.ord for x in prep] + [x.ord for x in neg] + [x.ord for x in refl]
				phrase_ords.sort()

				person = '3'
				if aux_past_tense:
					person = aux_past_tense[0].feats['Person']

				# In ru, be, uk, the person is not expressed in past tense and the verbform is Fin, not Part
				if cop[0].feats['VerbForm'] == 'Fin':
					person = ''
				
				self.write_node_info(node,
					aspect=cop[0].feats['Aspect'],
					tense=cop[0].feats['Tense'],
					person=person,
					number=cop[0].feats['Number'],
					mood='Ind',
					voice=self.get_voice(cop[0], refl),
					form='Fin',
					reflex=self.get_is_reflex(node,refl),
					polarity=self.get_polarity(cop[0],neg),
					ords=phrase_ords,
					gender=cop[0].feats['Gender'],
					animacy=cop[0].feats['Animacy']
					)
