"""
Morphosyntactic features (UniDive, Lenka Krippnerová):
This block detects present tense forms in Slavic languages and saves their
features as Phrase* attributes in MISC of their head word.
"""

import udapi.block.msf.phrase

class Present(udapi.block.msf.phrase.Phrase):

	def process_node(self,node):
		# the condition VerbForm == 'Fin' ensures that there are no transgressives between the found verbs
		# the aspect is not always given in Czech treebanks, so we can't rely on the fact that the imperfect aspect is specified 
		if node.feats['Tense'] == 'Pres' and node.upos == 'VERB' and node.feats['VerbForm'] == 'Fin' and node.feats['Aspect'] !='Perf': 
			
			aux_forb = [x for x in node.children if x.upos == 'AUX' and (x.lemma == 'ќе' or x.lemma == 'ще' or x.feats['Mood'] == 'Cnd')] # forbidden auxiliaries for present tense (these auxiliaries are used for the future tense or the conditional mood)

			if not aux_forb:
				refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']

				phrase_nodes = [node] + refl
				neg = self.get_negative_particles(phrase_nodes)
				phrase_nodes += neg

				phrase_ords = [x.ord for x in phrase_nodes]
				phrase_ords.sort()
				
				self.write_node_info(node,
					tense='Pres',
					person=node.feats['Person'],
					number=node.feats['Number'],
					mood='Ind',
					aspect=node.feats['Aspect'],
					voice=self.get_voice(node,refl),
					form='Fin',
					polarity=self.get_polarity(phrase_nodes),
					expl=self.get_expl_type(node,refl),
					analytic=self.get_analytic_bool(node),
					ords=phrase_ords
					)
				return

		# passive voice
		if node.upos == 'ADJ' and node.feats['Voice'] == 'Pass':
			aux = [x for x in node.children if x.udeprel == 'aux' and x.feats['Tense'] == 'Pres' and x.lemma != 'hteti' and x.lemma != 'htjeti']
			aux_forb = [x for x in node.children if x.udeprel == 'aux' and x.feats['Tense'] != 'Pres'] # we don't want the past passive (e. g. 'byl jsem poučen' in Czech)
			
			if aux and not aux_forb:
				phrase_nodes = [node] + aux
				neg = self.get_negative_particles(phrase_nodes)
				phrase_nodes += neg

				phrase_ords = [x.ord for x in phrase_nodes]
				phrase_ords.sort()

				auxVerb = aux[0]

				self.write_node_info(node,
					tense='Pres',
					person=auxVerb.feats['Person'],
					number=auxVerb.feats['Number'],
					mood='Ind',
					aspect=node.feats['Aspect'],
					form='Fin',
					voice='Pass',
					polarity=self.get_polarity(phrase_nodes),
					ords=phrase_ords,
					gender=node.feats['Gender'],
					animacy=node.feats['Animacy'],
					analytic=self.get_analytic_bool(node)
					)
				return
			
		# participles
		# in some languages, participles are used as attributes (they express case and degree)
		if node.upos == 'ADJ' and node.feats['VerbForm'] == 'Part':
			aux_forb = [x for x in node.children if x.udeprel == 'aux']
			cop = [x for x in node.children if x.udeprel == 'cop']
			
			if not aux_forb and not cop:
				refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']

				phrase_nodes = [node] + refl
				neg = self.get_negative_particles(phrase_nodes)
				phrase_nodes += neg

				phrase_ords = [x.ord for x in phrase_nodes]
				phrase_ords.sort()

				self.write_node_info(node,
					aspect=node.feats['Aspect'],
					tense=node.feats['Tense'],
					number=node.feats['Number'],
					form='Part',
					voice=self.get_voice(node, refl),
					expl=self.get_expl_type(node, refl),
					polarity=self.get_polarity(phrase_nodes),
					analytic=self.get_analytic_bool(node),
					ords=phrase_ords
				)
				return

		cop = [x for x in node.children if x.udeprel == 'cop' and x.feats['Tense'] == 'Pres']
		aux_forb = [x for x in node.children if x.upos == 'AUX' and x.feats['Tense'] != 'Pres'] # in Serbian this can be a future tense
					
		if cop and not aux_forb:
			aux = [x for x in node.children if x.udeprel == "aux" and x.feats['Mood'] == 'Ind' and x.feats['Tense'] == 'Pres']
			prep = [x for x in node.children if x.upos == 'ADP']
			refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']

			phrase_nodes = [node] + cop + aux + prep + refl
			neg = self.get_negative_particles(phrase_nodes)
			phrase_nodes += neg

			copVerb = cop[0]
				
			phrase_ords = [x.ord for x in phrase_nodes]
			phrase_ords.sort()
				
			self.write_node_info(node,
					aspect=copVerb.feats['Aspect'],
					tense='Pres',
					person=copVerb.feats['Person'],
					number=copVerb.feats['Number'],
					mood='Ind',
					form='Fin',
					voice=self.get_voice(copVerb, refl),
					expl=self.get_expl_type(node, refl),
					polarity=self.get_polarity(phrase_nodes),
					analytic=self.get_analytic_bool(node),
					ords=phrase_ords
				)
