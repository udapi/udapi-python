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
			neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']
			
			phrase_ords = [node.ord] + [x.ord for x in refl] + [x.ord for x in neg]
			phrase_ords.sort()
			
			self.write_node_info(node,
				person=node.feats['Person'],
				number=node.feats['Number'],
				aspect=node.feats['Aspect'],
				mood='Imp',
				form='Fin',
				voice='Act',
				polarity=self.get_polarity(node,neg),
				reflex=self.get_is_reflex(node,refl),
				ords=phrase_ords
				)
			return
			
		# verbs in the passive forms are marked as ADJ
		if node.upos == 'ADJ' and node.feats['Voice'] == 'Pass':
			aux = [x for x in node.children if x.udeprel == 'aux' and x.feats['Mood'] == 'Imp']
			if len(aux) > 0:
				neg = [x for x in node.children if x.feats['Polarity'] == 'Neg' and x.upos == 'PART']
				
				phrase_ords = [node.ord] + [x.ord for x in aux] + [x.ord for x in neg]
				phrase_ords.sort()
				
				self.write_node_info(node,
					person=aux[0].feats['Person'],
					number=aux[0].feats['Number'],
					mood='Imp',
					voice='Pass',
					aspect=node.feats['Aspect'],
					form='Fin',
					polarity=self.get_polarity(node,neg),
					ords=phrase_ords,
					gender=node.feats['Gender'],
					animacy=node.feats['Animacy']
					)
				return


		cop = [x for x in node.children if x.udeprel == 'cop' and x.feats['Mood'] == 'Imp']
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
				mood='Imp',
				form='Fin',
				voice=self.get_voice(copVerb, refl),
				reflex=self.get_is_reflex(node, refl),
				polarity=self.get_polarity(node,neg),
				ords=phrase_ords
				)

