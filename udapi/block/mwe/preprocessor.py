#!/usr/bin/env python3

from udapi.core.block import Block

class Preprocessor(Block):
		
	def process_node(self,node):
				
		# in Belarusian, some adjectives formed from verbs are marked as verbs
		# if the verb has case, then it is an adjective
		if node.upos == 'VERB' and node.feats['Case'] != '':
			node.upos = 'ADJ'
			
		# in Polish, the conditional mood for auxiliary verbs is marked as deprel == 'aux:cnd' and not as in the last Slavic languages ​​feats['Mood'] == 'Cnd'
		if node.deprel == 'aux:cnd':
			node.feats['Mood'] = 'Cnd'
			
		# sjednotit cas u dokonavych sloves vyjadrujici budoucnost
		# chceme pritomny, nebo budouci? - s budoucim by se asi zjednodusilo dost veci
		# jak ale poznat, ktery cas prepsat a ktery ne? - problem s makedonstinou
		
		# sjednotit passivum, rozhodnout, zda ma byt plnovyznamove sloveso znaceno jako ADJ, nebo VERB
			
		# unify polarities - some languages ​​mark only Neg (Russian), some mark both Neg and Pos (Czech)
		if node.feats['Polarity'] == 'Pos':
			node.feats['Polarity'] = ''
		
		# makedonstina tvori budouci cas pomoci pomocneho slova ќе, u nejz neni nijak vyznaceno, ze se podili na tvorbe budouciho casu
		# stejne tak bulharstina pomoci pomocneho slova ще
		# makedonstina a bulharstina
		if node.feats['Tense'] == 'Pres':
			aux = [x for x in node.children if x.lemma == 'ќе' or x.lemma == 'ще']
			if len(aux) == 1:
				aux[0].feats['Tense'] = 'Fut'
				
		# in Czech and in Old Church Slavonic, the participle is marked with the plural gender
		if node.feats['Gender'] == 'Fem,Neut' or node.feats['Gender'] == 'Fem,Masc':
			subj = [x for x in node.children if x.udeprel == 'nsubj']

			# for relative pronouns, only one gender is indicated
			if len(subj) == 1:
				conj = [x for x in subj[0].children if x.deprel == 'conj']
				if len(conj) == 0:
					node.feats['Gender'] = subj[0].feats['Gender']
					node.feats['Number'] = subj[0].feats['Number']
				
