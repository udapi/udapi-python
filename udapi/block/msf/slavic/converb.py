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
			neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']
			
			phrase_ords = [node.ord] + [x.ord for x in refl] + [x.ord for x in neg]
			phrase_ords.sort()
			
			self.write_node_info(node,
				person=node.feats['Person'],
				number=node.feats['Number'],
				form='Conv',
				tense=node.feats['Tense'],
				aspect=node.feats['Aspect'],
				polarity=self.get_polarity(node,neg),
				reflex=self.get_is_reflex(node,refl),
				ords=phrase_ords,
				gender=node.feats['Gender'],
				animacy=node.feats['Animacy'],
				voice=self.get_voice(node, refl)
				)

		# passive voice
		elif node.upos == 'ADJ':
			aux = [x for x in node.children if x.udeprel == 'aux' and x.feats['VerbForm'] == 'Conv']
			
			if len(aux) > 0:
				neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']
				auxVerb = aux[0]
				phrase_ords = [node.ord] + [x.ord for x in aux] + [x.ord for x in neg]
				phrase_ords.sort()
			
				self.write_node_info(node,
					person=auxVerb.feats['Person'],
					number=auxVerb.feats['Number'],
					form='Conv',
					tense=auxVerb.feats['Tense'],
					aspect=node.feats['Aspect'],
					polarity=self.get_polarity(auxVerb,neg),
					ords=phrase_ords,
					gender=auxVerb.feats['Gender'],
					animacy=auxVerb.feats['Animacy'],
					voice='Pass'
				)

		# copulas
		else:
			cop = [x for x in node.children if x.udeprel == 'cop' and x.feats['VerbForm'] == 'Conv']
			
			if len(cop) > 0:
				prep = [x for x in node.children if x.upos == 'ADP']
				neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']
				refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']
			
				copVerb = cop[0]
				phrase_ords = [node.ord] + [x.ord for x in cop] + [x.ord for x in prep] + [x.ord for x in neg] + [x.ord for x in refl]
				phrase_ords.sort()

				
				self.write_node_info(node,
					person=copVerb.feats['Person'],
					number=copVerb.feats['Number'],
					tense=copVerb.feats['Tense'],
					gender=copVerb.feats['Gender'],
					animacy=copVerb.feats['Animacy'],
					form='Conv',
					polarity=self.get_polarity(node,neg),
					ords=phrase_ords,
					voice=self.get_voice(copVerb, refl)
					)

