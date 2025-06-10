"""
Morphosyntactic features (UniDive, Lenka Krippnerová):
This block detects future tense forms in Slavic languages and saves their
features as Phrase* attributes in MISC of their head word.
"""

import udapi.block.msf.phrase

class Future(udapi.block.msf.phrase.Phrase):
	
	def process_node(self, node):
		# future tense for Serbian and Croatian
		aux = [x for x in node.children if x.udeprel == 'aux' and x.feats['Tense'] == 'Pres' and (x.lemma == 'hteti' or x.lemma == 'htjeti')]
		if node.upos != 'AUX' and aux:
			refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']
			aux_other = [x for x in node.children if x.udeprel == 'aux'] # adding aux for passive voice
			cop = [x for x in node.children if x.deprel == 'cop']

			phrase_nodes = [node] + refl + aux_other + cop
			neg = self.get_negative_particles(phrase_nodes)
			phrase_nodes += neg

			phrase_ords = [x.ord for x in phrase_nodes]
			phrase_ords.sort()
			
			
			if not cop:
				self.write_node_info(node, 
					tense='Fut',
					person=aux[0].feats['Person'],
					number=aux[0].feats['Number'],
					mood='Ind',
					voice=node.feats['Voice'],
					aspect=node.feats['Aspect'], # srbstina ani chorvatstina vidy nema
					form='Fin',
					polarity=self.get_polarity(phrase_nodes),
					reflex=self.get_is_reflex(node,refl),
					gender=node.feats['Gender'],
					animacy=node.feats['Animacy'],
					ords=phrase_ords
					)
			else:
				prep = [x for x in node.children if x.upos == 'ADP']
				phrase_nodes += prep
				phrase_ords += [x.ord for x in prep]
				phrase_ords.sort()

				self.write_node_info(node, 
					tense='Fut',
					person=aux[0].feats['Person'],
					number=aux[0].feats['Number'],
					mood='Ind',
					voice=node.feats['Voice'],
					aspect=node.feats['Aspect'], 
					form='Fin',
					polarity=self.get_polarity(phrase_nodes),
					reflex=self.get_is_reflex(node,refl),
					gender=node.feats['Gender'],
					animacy=node.feats['Animacy'],
					ords=phrase_ords
					)
				
			return
				
		# Macedonian forms the future tense with the auxiliary word ќе and a verb in the present tense
		# Bulgarian forms the future tense with the auxiliary word ще and a verb in the present tense
		aux = [x for x in node.children if x.lemma == 'ќе' or x.lemma == 'ще']
		
		if node.feats['Tense'] == 'Pres' and aux:
			refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']

			phrase_nodes = [node] + refl + aux
			neg = self.get_negative_particles(phrase_nodes)
			phrase_nodes += neg

			phrase_ords = [x.ord for x in phrase_nodes]
			phrase_ords.sort()
			
			self.write_node_info(node, 
				tense='Fut',
				person=node.feats['Person'],
				number=node.feats['Number'],
				mood='Ind',
				voice=node.feats['Voice'],
				aspect=node.feats['Aspect'],
				form='Fin',
				polarity=self.get_polarity(phrase_nodes),
				reflex=self.get_is_reflex(node,refl),
				ords=phrase_ords
				)
			return

		# future tense of perfect verbs
		# Upper Sorbian forms the future tense in this way, however, the feats[Aspect] are not listed in the data
		# in some languages ​​(e.g. in Russian) these verbs have the Tense Fut, in others (e.g. in Czech) they have the Tense Pres
		"""if node.feats['Aspect'] == 'Perf' and (node.feats['Tense'] == 'Pres' or node.feats['Tense'] == 'Fut') and node.feats['VerbForm'] != 'Conv':
			refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']
			
			phrase_nodes = [node] + refl
			neg = self.get_negative_particles(phrase_nodes)
			phrase_nodes += neg
			
			phrase_ords = [x.ord for x in phrase_nodes]
			phrase_ords.sort()
			
			self.write_node_info(node, 
				tense='Fut',
				person=node.feats['Person'],
				number=node.feats['Number'],
				mood='Ind',
				voice=self.get_voice(node,refl),
				form='Fin',
				aspect='Perf',
				polarity=self.get_polarity(phrase_nodes),
				reflex=self.get_is_reflex(node,refl),
				ords=phrase_ords
				)
			return"""

		
		# future tense of imperfect verbs and passive voice
		# in some languages ​​the verb is in the infinitive, in some it is in the l-participle
		# the condition node.upos == 'ADJ' is due to the passive voice - the n-participle is marked as ADJ, but the auxiliary verb is not cop, but aux
		if node.upos == 'VERB' or node.upos == 'ADJ':
			
			aux = [x for x in node.children if x.udeprel == 'aux' and x.feats['Tense'] == 'Fut']
			
			refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']
			
			phrase_nodes = [node] + aux + refl
			neg = self.get_negative_particles(phrase_nodes)
			phrase_nodes += neg

			phrase_ords = [x.ord for x in phrase_nodes]
			phrase_ords.sort()

			if aux:
				auxVerb = aux[0]
				self.write_node_info(node,
					tense='Fut',
					person=auxVerb.feats['Person'],
					number=auxVerb.feats['Number'],
					mood='Ind',
					voice=self.get_voice(node,refl),
					aspect=node.feats['Aspect'],
					form='Fin',
					polarity=self.get_polarity(phrase_nodes),
					reflex=self.get_is_reflex(node,refl),
					ords=phrase_ords,
					gender=node.feats['Gender'],
					animacy=node.feats['Animacy']
					)
				return

			# simple future tense - e.g. in Serbian, the future tense can be formed by combining a verb with a full meaning and an auxiliary verb into one word, i.e. without an auxiliary verb
			# or verbs like pojede, půjdeme... in Czech
			
			if not aux and node.feats['Tense'] == 'Fut':
						
				self.write_node_info(node,
					tense='Fut',
					person=node.feats['Person'],
					number=node.feats['Number'],
					mood='Ind',
					voice=self.get_voice(node,refl),
					aspect=node.feats['Aspect'],
					form='Fin',
					polarity=self.get_polarity(phrase_nodes),
					reflex=self.get_is_reflex(node,refl),
					ords=phrase_ords
					)
				return
				
				
		cop = [x for x in node.children if x.udeprel == 'cop' and x.feats['Tense'] == 'Fut']
		if cop:
			copVerb = cop[0]
			aux = [x for x in node.children if x.udeprel == 'aux' and x.feats['Mood']=='Ind']
			prep = [x for x in node.children if x.upos == 'ADP']
			refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']

			phrase_nodes = [node] + cop + aux + prep + refl
			neg = self.get_negative_particles(phrase_nodes)
			phrase_nodes += neg

			phrase_ords = [x.ord for x in phrase_nodes]
			phrase_ords.sort()
				
			self.write_node_info(node,
					aspect=copVerb.feats['Aspect'],
					tense='Fut',
					person=copVerb.feats['Person'],
					number=copVerb.feats['Number'],
					mood='Ind',
					form='Fin',
					voice=self.get_voice(copVerb, refl),
					polarity=self.get_polarity(phrase_nodes),
					ords=phrase_ords
				)

