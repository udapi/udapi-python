"""
Morphosyntactic features (UniDive, Lenka Krippnerová):
This block detects past tense forms in Slavic languages and saves their
features as Phrase* attributes in MISC of their head word.
"""

import udapi.block.msf.phrase

class Past(udapi.block.msf.phrase.Phrase):

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
			
			phrase_nodes = [node] + refl
			neg = self.get_negative_particles(phrase_nodes)
			phrase_nodes += neg

			phrase_ords = [x.ord for x in phrase_nodes]
			phrase_ords.sort()

			self.write_node_info(node,
						tense=node.feats['Tense'],
						person=node.feats['Person'],
						number=node.feats['Number'],
						mood=node.feats['Mood'],
						voice='Act', #In Polish, impersonal statements are annotated with Voice=Act. In Ukrainian, the Voice feature is missing; therefore, we decided to annotate these phrases with PhraseVoice=Act
						aspect=node.feats['Aspect'],
						form=node.feats['VerbForm'],
						polarity=self.get_polarity(phrase_nodes),
						expl=self.get_expl_type(node,refl),
						ords=phrase_ords,
						gender=node.feats['Gender'],
						animacy=node.feats['Animacy'],
						periphrasis=self.get_periphrasis_bool(node)
						)

		# compound past tense
		if (node.feats['VerbForm'] in ['Part', 'PartRes', 'Fin']) and node.upos == 'VERB' and node.feats['Voice'] != 'Pass':
			aux = [x for x in node.children if x.udeprel == 'aux' and x.feats['Tense'] in ['Pres', '']]
			aux_pqp = [x for x in node.children if x.udeprel == 'aux' and x.feats['Tense'] in past_tenses]
			refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']

			phrase_nodes = [node] + aux + refl + aux_pqp
			neg = self.get_negative_particles(phrase_nodes)
			phrase_nodes += neg
			
			phrase_ords = [x.ord for x in phrase_nodes]
			phrase_ords.sort()
			
			aux_cnd = [x for x in node.children if (x.feats['Mood'] == 'Cnd' or x.deprel == 'aux:cnd') and x.udeprel != 'conj'] # we don't want to mark l-participles in the conditional as past tense
			if not aux_cnd:
				if aux:
					person = aux[0].feats['Person']

				elif not aux:
					person = '3'

				if aux_pqp:
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
						polarity=self.get_polarity(phrase_nodes),
						expl=self.get_expl_type(node,refl),
						ords=phrase_ords,
						gender=node.feats['Gender'],
						animacy=node.feats['Animacy'],
						periphrasis=self.get_periphrasis_bool(node)
						)
				

		# the past tense of some Slavic languages ​​is formed only by a verb without an auxiliary verb (e.g. Polish)
		# or imperfect (special case of the past tense) e.g. in Bulgarian or Croatian 
		elif (node.feats['Tense'] in past_tenses) and node.upos == 'VERB' and node.feats['VerbForm'] != 'Conv':

			# the past tense is formed only by a content verb, not with an auxiliary
			aux_forb = [x for x in node.children if x.udeprel == 'aux']
			
			if not aux_forb:

				refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']

				phrase_nodes = [node] + refl
				neg = self.get_negative_particles(phrase_nodes)
				phrase_nodes += neg
			
				phrase_ords = [x.ord for x in phrase_nodes]
				phrase_ords.sort()

				self.write_node_info(node,
					tense=node.feats['Tense'],
					person=node.feats['Person'],
					number=node.feats['Number'],
					mood='Ind',
					voice=self.get_voice(node,refl),
					aspect=node.feats['Aspect'],
					form=node.feats['VerbForm'],
					polarity=self.get_polarity(phrase_nodes),
					expl=self.get_expl_type(node,refl),
					ords=phrase_ords,
					gender=node.feats['Gender'],
					animacy=node.feats['Animacy'],
					periphrasis=self.get_periphrasis_bool(node)
					)
			
				
			
		# passive
		elif node.upos == 'ADJ' and node.feats['Voice'] == 'Pass' and not cop:	
			aux_past_tense = [x for x in node.children if x.udeprel == 'aux' and (x.feats['Tense'] in past_tenses)]
			aux_cnd = [x for x in node.children if x.feats['Mood'] == 'Cnd' or x.deprel == 'aux:cnd'] # we don't want to mark l-participles in the conditional as past tense
			if not aux_cnd:
				if aux_past_tense:
					aux_pres_tense = [x for x in  node.children if x.udeprel == 'aux' and x.feats['Tense'] == 'Pres'] # e. g. the auxiliary 'jsem' in the phrase 'byl jsem přinucen'
					
					phrase_nodes = [node] + aux_past_tense + aux_pres_tense
					neg = self.get_negative_particles(phrase_nodes)
					phrase_nodes += neg

					phrase_ords = [x.ord for x in phrase_nodes]
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
						polarity=self.get_polarity(phrase_nodes),
						ords=phrase_ords,
						gender=node.feats['Gender'],
						animacy=node.feats['Animacy'],
						periphrasis=self.get_periphrasis_bool(node)
						)
				
		else:
			aux_cnd = [x for x in node.children if x.feats['Mood'] == 'Cnd' or x.deprel == 'aux:cnd'] # we don't want to mark l-participles in the conditional as past tense
			if cop and not aux_cnd:
				aux_past_tense = [x for x in node.children if x.udeprel == 'aux' and x.feats['Tense'] == 'Pres']
				prep = [x for x in node.children if x.upos == 'ADP']
				refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']

				phrase_nodes = [node] + aux_past_tense + cop + prep + refl
				neg = self.get_negative_particles(phrase_nodes)
				phrase_nodes += neg

				phrase_ords = [x.ord for x in phrase_nodes]
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
					expl=self.get_expl_type(node,refl),
					polarity=self.get_polarity(phrase_nodes),
					ords=phrase_ords,
					gender=cop[0].feats['Gender'],
					animacy=cop[0].feats['Animacy'],
					periphrasis=self.get_periphrasis_bool(node)
					)
