"""
Morphosyntactic features (UniDive, Lenka Krippnerová):
This block detects future tense forms in Slavic languages and saves their
features as Phrase* attributes in MISC of their head word.
"""

import udapi.block.mwe.msfphrase

class Future(udapi.block.mwe.msfphrase.MsfPhrase):
	
	def process_node(self, node):
		# future tense for Serbian and Croatian
		aux = [x for x in node.children if x.udeprel == 'aux' and x.feats['Tense'] == 'Pres' and (x.lemma == 'hteti' or x.lemma == 'htjeti')]
		if node.upos != 'AUX' and len(aux) != 0:
			refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']
			neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']
			aux_other = [x for x in node.children if x.udeprel == 'aux'] # adding aux for passive voice
			cop = [x for x in node.children if x.deprel == 'cop']
			phrase_ords = [node.ord] + [x.ord for x in refl] + [x.ord for x in neg] + [x.ord for x in aux_other] + [x.ord for x in cop]
			phrase_ords.sort()
			
			# u infinitivu neni vyznacen slovesny rod
			# PhraseVoice ale chceme nastavit na activum, jelikoz se jedna o pomocne sloveso + infinitiv
			voice=node.feats['Voice']
			#if voice == '':
			#	voice = 'Act'
			if len(cop) == 0:
				self.write_node_info(node, 
					tense='Fut',
					person=aux[0].feats['Person'],
					number=aux[0].feats['Number'],
					mood='Ind',
					voice=voice,
					aspect=node.feats['Aspect'], # srbstina ani chorvatstina vidy nema
					form='Fin',
					polarity=self.get_polarity(node,neg),
					reflex=self.get_is_reflex(node,refl),
					gender=node.feats['Gender'],
					animacy=node.feats['Animacy'],
					ords=phrase_ords
					)
			else:
				prep = [x for x in node.children if x.upos == 'ADP']
				phrase_ords += [x.ord for x in prep]
				phrase_ords.sort()

				self.write_node_info(node, 
					tense='Fut',
					person=aux[0].feats['Person'],
					number=aux[0].feats['Number'],
					mood='Ind',
					voice=voice,
					aspect=node.feats['Aspect'], 
					form='Fin',
					polarity=self.get_polarity(node,neg),
					reflex=self.get_is_reflex(node,refl),
					gender=node.feats['Gender'],
					animacy=node.feats['Animacy'],
					ords=phrase_ords
					)
				
			return
				
		# Macedonian forms the future tense with the auxiliary word ќе and a verb in the present tense
		# Bulgarian forms the future tense with the auxiliary word ще and a verb in the present tense
		aux = [x for x in node.children if x.lemma == 'ќе' or x.lemma == 'ще']
		
		if node.feats['Tense'] == 'Pres' and len(aux) > 0:
			refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']
			neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']
			phrase_ords = [node.ord] + [x.ord for x in refl] + [x.ord for x in neg] + [x.ord for x in aux]
			phrase_ords.sort()
			
			self.write_node_info(node, 
				tense='Fut',
				person=node.feats['Person'],
				number=node.feats['Number'],
				mood='Ind',
				voice=node.feats['Voice'],
				aspect=node.feats['Aspect'],
				form='Fin',
				polarity=self.get_polarity(node,neg),
				reflex=self.get_is_reflex(node,refl),
				ords=phrase_ords
				)
			return

		# future tense of perfect verbs
		# Upper Sorbian forms the future tense in this way, however, the feats[Aspect] are not listed in the data
		# in some languages ​​(e.g. in Russian) these verbs have the Tense Fut, in others (e.g. in Czech) they have the Tense Pres
		"""if node.feats['Aspect'] == 'Perf' and (node.feats['Tense'] == 'Pres' or node.feats['Tense'] == 'Fut') and node.feats['VerbForm'] != 'Conv':
			refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']
			
			neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']
			
			phrase_ords = [node.ord] + [x.ord for x in refl] + [x.ord for x in neg]
			phrase_ords.sort()
			
			self.write_node_info(node, 
				tense='Fut',
				person=node.feats['Person'],
				number=node.feats['Number'],
				mood='Ind',
				voice=self.get_voice(node,refl),
				form='Fin',
				aspect='Perf',
				polarity=self.get_polarity(node,neg),
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
			neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']
			if len(aux) > 0:
				auxVerb = aux[0]
				phrase_ords = [node.ord] + [x.ord for x in aux] + [x.ord for x in refl] + [x.ord for x in neg]
				phrase_ords.sort()
				self.write_node_info(node,
					tense='Fut',
					person=auxVerb.feats['Person'],
					number=auxVerb.feats['Number'],
					mood='Ind',
					voice=self.get_voice(node,refl),
					aspect=node.feats['Aspect'],
					form='Fin',
					polarity=self.get_polarity(auxVerb,neg),
					reflex=self.get_is_reflex(node,refl),
					ords=phrase_ords,
					gender=node.feats['Gender'],
					animacy=node.feats['Animacy']
					)
				return

			# simple future tense - e.g. in Serbian, the future tense can be formed by combining a verb with a full meaning and an auxiliary verb into one word, i.e. without an auxiliary verb
			# or verbs like pojede, půjdeme... in Czech
			
			if len(aux) == 0 and node.feats['Tense'] == 'Fut':
				
				phrase_ords = [node.ord] + [x.ord for x in refl] + [x.ord for x in neg]
				phrase_ords.sort()
				
				self.write_node_info(node,
					tense='Fut',
					person=node.feats['Person'],
					number=node.feats['Number'],
					mood='Ind',
					voice=self.get_voice(node,refl), # passivum se muze objevit (napr. pojede se), ale jmenny rod neni vyjadren
					aspect=node.feats['Aspect'],
					form='Fin',
					polarity=self.get_polarity(node,neg),
					reflex=self.get_is_reflex(node,refl),
					ords=phrase_ords
					)
				return
				
				
		cop = [x for x in node.children if x.udeprel == 'cop' and x.feats['Tense'] == 'Fut']
		if len(cop) > 0:
			copVerb = cop[0]
			aux = [x for x in node.children if x.udeprel == 'aux' and x.feats['Mood']=='Ind']
			prep = [x for x in node.children if x.upos == 'ADP']
			neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']
			refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']

			phrase_ords = [node.ord] + [x.ord for x in cop] + [x.ord for x in aux] + [x.ord for x in prep] + [x.ord for x in neg] + [x.ord for x in refl]
			phrase_ords.sort()
				
			self.write_node_info(node,
					tense='Fut',
					person=copVerb.feats['Person'],
					number=copVerb.feats['Number'],
					mood='Ind',
					form='Fin',
					voice=self.get_voice(copVerb, refl),
					polarity=self.get_polarity(copVerb,neg),
					ords=phrase_ords
				)

