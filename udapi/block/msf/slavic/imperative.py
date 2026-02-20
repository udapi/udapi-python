"""
Morphosyntactic features (UniDive, Lenka Krippnerová):
This block detects imperative verb forms in Slavic languages and saves their
features as Phrase* attributes in MISC of their head word.
"""

import udapi.block.msf.phrase

class Imperative(udapi.block.msf.phrase.Phrase):

	def process_node(self, node):
		# the condition node.upos == 'VERB' ensures that copulas do not enter this branch
		if node.feats['Mood'] == 'Imp' and node.upos == 'VERB':
			refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']
			
			phrase_nodes = [node] + refl
			neg = self.get_negative_particles(phrase_nodes)
			phrase_nodes += neg
			
			phrase_ords = [x.ord for x in phrase_nodes]
			phrase_ords.sort()
			
			self.write_node_info(node,
				person=node.feats['Person'],
				number=node.feats['Number'],
				aspect=node.feats['Aspect'],
				mood='Imp',
				form='Fin',
				voice='Act',
				polarity=self.get_polarity(phrase_nodes),
				expl=self.get_expl_type(node,refl),
				analytic=self.get_analytic_bool(node),
				ords=phrase_ords
				)
			return
			
		# verbs in the passive forms are marked as ADJ
		if node.upos == 'ADJ' and node.feats['Voice'] == 'Pass':
			aux = [x for x in node.children if x.udeprel == 'aux' and x.feats['Mood'] == 'Imp']
			if aux:
				phrase_nodes = [node] + aux
				neg = self.get_negative_particles(phrase_nodes)
				phrase_nodes += neg
				
				phrase_ords = [x.ord for x in phrase_nodes]
				phrase_ords.sort()
				
				self.write_node_info(node,
					person=aux[0].feats['Person'],
					number=aux[0].feats['Number'],
					mood='Imp',
					voice='Pass',
					aspect=node.feats['Aspect'],
					form='Fin',
					polarity=self.get_polarity(phrase_nodes),
					ords=phrase_ords,
					gender=node.feats['Gender'],
					animacy=node.feats['Animacy'],
					analytic=self.get_analytic_bool(node)
					)
				return


		cop = [x for x in node.children if x.udeprel == 'cop' and x.feats['Mood'] == 'Imp']
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
				mood='Imp',
				form='Fin',
				voice=self.get_voice(copVerb, refl),
				expl=self.get_expl_type(node, refl),
				polarity=self.get_polarity(phrase_nodes),
				analytic=self.get_analytic_bool(node),
				ords=phrase_ords
				)
