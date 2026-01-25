"""
Morphosyntactic features (UniDive, Lenka Krippnerová):
This block detects conditional verb forms in Slavic languages and saves their
features as Phrase* attributes in MISC of their head word.
"""

import udapi.block.msf.phrase

class Conditional(udapi.block.msf.phrase.Phrase):
	
	def process_node(self, node):
		if (node.feats['VerbForm'] == 'Part' or node.feats['VerbForm'] == 'PartRes') or node.feats['VerbForm'] == 'Fin':
			# in most Slavic languages, the verb has feats['VerbForm'] == 'Part' but in Polish the verb has feats['VerbForm'] == 'Fin'
			
			aux_cnd = [x for x in node.children if x.feats['Mood'] == 'Cnd' or x.deprel == 'aux:cnd'] # list for auxiliary verbs for forming the conditional mood
			cop = [x for x in node.children if x.udeprel == 'cop'] # in some cases it may happen that the cop follows the noun, we don't want to these cases in this branch
			# in Polish the auxiliary verbs for conditional mood have deprel == 'aux:cnd', in other languages the auxiliary verbs have x.feats['Mood'] == 'Cnd'
			
			# the conditional mood can be formed using the auxiliary verb or some conjunctions (such as 'aby, kdyby...' in Czech)
			# so x.udeprel == 'aux' can't be required because it doesn't meet the conjunctions
			
			if aux_cnd and not cop:
				aux = [x for x in node.children if x.udeprel == 'aux' or x.feats['Mood'] == 'Cnd'] # all auxiliary verbs and conjuctions with feats['Mood'] == 'Cnd'
				refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']

				phrase_nodes = [node] + aux + refl
				
				neg = self.get_negative_particles(phrase_nodes)
				phrase_nodes += neg

				phrase_ords = [x.ord for x in phrase_nodes]
				phrase_ords.sort()
			
				auxVerb = aux_cnd[0]

				person='3' # TODO there is a problem in russian etc. (same as in past tense)
				if auxVerb.feats['Person'] != '':
					person=auxVerb.feats['Person']
				
					
				self.write_node_info(node,
					person=person,
					number=node.feats['Number'],
					mood='Cnd',
					form='Fin',
					aspect=node.feats['Aspect'],
					expl=self.get_expl_type(node,refl),
					polarity=self.get_polarity(phrase_nodes),
					voice=self.get_voice(node, refl),
					ords=phrase_ords,
					gender=node.feats['Gender'],
					animacy=node.feats['Animacy'],
					analytic=self.get_analytic_bool(node)
				)
				return
		
					
		cop = [x for x in node.children if x.udeprel == 'cop' and (x.feats['VerbForm'] == 'Part' or x.feats['VerbForm'] == 'Fin')]
		aux_cnd = [x for x in node.children if x.feats['Mood'] == 'Cnd' or x.deprel=='aux:cnd']
			
		if cop and aux_cnd:
			# there can be a copula with Mood='Cnd' (i. e. in Old East Slavonic), we don't want to count these copula in phrase_ords twice, so there is x.udeprel != 'cop' in aux list
			aux = [x for x in node.children if (x.udeprel == 'aux' or x.feats['Mood'] == 'Cnd') and x.udeprel != 'cop']
			prep = [x for x in node.children if x.upos == 'ADP']
			refl = [x for x in node.children if x.feats['Reflex'] == 'Yes' and x.udeprel == 'expl']

			phrase_nodes = [node] + aux + prep + refl + cop
			neg = self.get_negative_particles(phrase_nodes)
			phrase_nodes += neg

			copVerb = cop[0]
			phrase_ords = [x.ord for x in phrase_nodes]
			phrase_ords.sort()
			self.write_node_info(node,
					aspect=copVerb.feats['Aspect'],
					person=copVerb.feats['Person'],
					number=copVerb.feats['Number'],
					mood='Cnd',
					form='Fin',
					voice=self.get_voice(copVerb, refl),
					polarity=self.get_polarity(phrase_nodes),
					expl=self.get_expl_type(node, refl),
					ords=phrase_ords,
					gender=copVerb.feats['Gender'],
					animacy=copVerb.feats['Animacy'],
					analytic=self.get_analytic_bool(node)
			)