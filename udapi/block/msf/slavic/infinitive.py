"""
Morphosyntactic features (UniDive, Lenka Krippnerová):
This block detects infinitive verb forms in Slavic languages and saves their
features as Phrase* attributes in MISC of their head word.
"""

import udapi.block.msf.phrase

class Infinitive(udapi.block.msf.phrase.Phrase):

	def process_node(self,node):
		if node.feats['VerbForm'] == 'Inf' and node.upos == 'VERB':
			aux = [x for x in node.children if x.udeprel == 'aux']
			if not aux: # the list of auxiliary list must be empty - we don't want to mark infinitives which are part of any other phrase (for example the infinititive is part of the future tense in Czech)
				refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']
				
				phrase_nodes = [node] + refl
				neg = self.get_negative_particles(phrase_nodes)
				phrase_nodes == neg
				
				phrase_ords = [x.ord for x in phrase_nodes]
				phrase_ords.sort()
				
		
				self.write_node_info(node,
					aspect=node.feats['Aspect'],
					voice=self.get_voice(node,refl),
					form='Inf',
					polarity=self.get_polarity(phrase_nodes),
					expl=self.get_expl_type(node,refl),
					ords=phrase_ords
				)
				return
		
		if node.upos == 'ADJ' and node.feats['Voice'] == 'Pass':
			aux = [x for x in node.children if x.udeprel == 'aux' and x.feats['VerbForm'] == 'Inf']
			aux_forb = [x for x in node.children if x.udeprel == 'aux' and x.feats['VerbForm'] != 'Inf']
			if aux and not aux_forb:
				refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']

				phrase_nodes = [node] + aux + refl
				neg = self.get_negative_particles(phrase_nodes)
				phrase_nodes += neg

				phrase_ords = [x.ord for x in phrase_nodes]
				phrase_ords.sort()
				
				self.write_node_info(node,
					aspect=node.feats['Aspect'],
					voice='Pass',
					form='Inf',
					polarity=self.get_polarity(phrase_nodes),
					expl=self.get_expl_type(node, refl),
					ords=phrase_ords,
					gender=node.feats['Gender'],
					animacy=node.feats['Animacy'],
					number=node.feats['Number']
					)
				return
					
		

		cop = [x for x in node.children if x.udeprel == 'cop' and x.feats['VerbForm'] == 'Inf']
		aux_forb = [x for x in node.children if x.udeprel == 'aux']
		if cop and not aux_forb:
			prep = [x for x in node.children if x.upos == 'ADP']
			refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']

			phrase_nodes = [node] + cop + prep + refl
			neg = self.get_negative_particles(phrase_nodes)
			phrase_nodes += neg

			phrase_ords = [x.ord for x in phrase_nodes]
			phrase_ords.sort()
			
			self.write_node_info(node,
				aspect=cop[0].feats['Aspect'],
				voice=self.get_voice(cop[0], refl),
				form='Inf',
				polarity=self.get_polarity(phrase_nodes),
				expl=self.get_expl_type(node, refl),
				ords=phrase_ords
				)
			
		# there is a rare verb form called supine in Slovenian, it is used instead of infinitive as the argument of motion verbs
		if node.feats['VerbForm'] == 'Sup':
			refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']
			
			phrase_nodes = [node] + refl
			neg = self.get_negative_particles(phrase_nodes)
			phrase_nodes += neg

			phrase_ords = [x.ord for x in phrase_nodes]
			phrase_ords.sort()

			self.write_node_info(node,
					aspect=node.feats['Aspect'],
					voice='Act',
					form='Sup',
					polarity=self.get_polarity(phrase_nodes),
					expl=self.get_expl_type(node, refl),
					ords=phrase_ords
					)
