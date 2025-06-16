"""
Morphosyntactic features (UniDive, Lenka Krippnerová):
This block detects converb (transgressive) forms in Slavic languages and saves their
features as Phrase* attributes in MISC of their head word.
"""

import udapi.block.msf.phrase

class Converb(udapi.block.msf.phrase.Phrase):

	def process_node(self, node):
		# condition node.upos == 'VERB' to prevent copulas from entering this branch
		if node.feats['VerbForm'] == 'Conv' and node.upos == 'VERB':
			refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']

			phrase_nodes = [node] + refl
			neg = self.get_negative_particles(phrase_nodes)
			phrase_nodes += neg

			phrase_ords = [x.ord for x in phrase_nodes]
			phrase_ords.sort()
			
			self.write_node_info(node,
				person=node.feats['Person'],
				number=node.feats['Number'],
				form='Conv',
				tense=node.feats['Tense'],
				aspect=node.feats['Aspect'],
				polarity=self.get_polarity(phrase_nodes),
				reflex=self.get_is_reflex(node,refl),
				ords=phrase_ords,
				gender=node.feats['Gender'],
				animacy=node.feats['Animacy'],
				voice=self.get_voice(node, refl)
				)

		# passive voice
		elif node.upos == 'ADJ':
			aux = [x for x in node.children if x.udeprel == 'aux' and x.feats['VerbForm'] == 'Conv']
			
			if aux:
				auxVerb = aux[0]

				phrase_nodes = [node] + aux
				neg = self.get_negative_particles(phrase_nodes)
				phrase_nodes += neg
				phrase_ords = [x.ord for x in phrase_nodes]
				phrase_ords.sort()
			
				self.write_node_info(node,
					person=auxVerb.feats['Person'],
					number=auxVerb.feats['Number'],
					form='Conv',
					tense=auxVerb.feats['Tense'],
					aspect=node.feats['Aspect'],
					polarity=self.get_polarity(phrase_nodes),
					ords=phrase_ords,
					gender=auxVerb.feats['Gender'],
					animacy=auxVerb.feats['Animacy'],
					voice='Pass'
				)

		# copulas
		else:
			cop = [x for x in node.children if x.udeprel == 'cop' and x.feats['VerbForm'] == 'Conv']
			
			if cop:
				prep = [x for x in node.children if x.upos == 'ADP']
				refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']
			
				copVerb = cop[0]

				phrase_nodes = [node] + cop + prep + refl
				neg = self.get_negative_particles(phrase_nodes)
				phrase_nodes += neg
				phrase_ords = [x.ord for x in phrase_nodes]
				phrase_ords.sort()

				
				self.write_node_info(node,
					aspect=copVerb.feats['Aspect'],
					person=copVerb.feats['Person'],
					number=copVerb.feats['Number'],
					tense=copVerb.feats['Tense'],
					gender=copVerb.feats['Gender'],
					animacy=copVerb.feats['Animacy'],
					form='Conv',
					polarity=self.get_polarity(phrase_nodes),
					ords=phrase_ords,
					voice=self.get_voice(copVerb, refl)
					)
