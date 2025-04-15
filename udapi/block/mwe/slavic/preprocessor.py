#!/usr/bin/env python3

from udapi.core.block import Block

class Preprocessor(Block):
		
	def process_node(self,node):

		# in Ukrainian the active verb forms are not marked as PhraseVoice=Act
		if (node.upos == 'VERB' or (node.upos == 'AUX' and node.feats['VerbForm'] == 'Fin')) and node.feats['Voice'] == '':
			node.feats['Voice'] = 'Act'
				
		# in Belarusian, some adjectives formed from verbs are marked as verbs
		# if the verb has case, then it is an adjective
		if node.upos == 'VERB' and node.feats['Case'] != '':
			node.upos = 'ADJ'
			
		# in Polish, the conditional mood for auxiliary verbs is marked as deprel == 'aux:cnd' and not as in the last Slavic languages ​​feats['Mood'] == 'Cnd'
		if node.deprel == 'aux:cnd':
			node.feats['Mood'] = 'Cnd'
			
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
				
		# in Czech and in Old Church Slavonic, the participles are sometimes marked with the plural gender
		if node.feats['Gender'] == 'Fem,Neut' or node.feats['Gender'] == 'Fem,Masc':
			subj = [x for x in node.children if x.udeprel == 'nsubj']

			# for relative pronouns, only one gender is indicated
			if len(subj) == 1:
				conj = [x for x in subj[0].children if x.deprel == 'conj']
				if len(conj) == 0:
					node.feats['Gender'] = subj[0].feats['Gender']
					node.feats['Number'] = subj[0].feats['Number']

		# participles in passive are sometimes annotated as VERB, sometimes as ADJ
		if node.upos == 'VERB' and node.feats['Voice'] == 'Pass':
			node.upos = 'ADJ'

		# there are cases where the node has deprel=='expl:pv' or 'expl:pass' or 'expl:impers' and Reflex is not Yes (i.e. Macedonian treebank)
		# we add the Reflex=Yes feature
		if node.deprel == 'expl:pv' or node.deprel == 'expl:pass' or node.deprel == 'expl:impers':
			node.feats['Reflex'] = 'Yes'

		# fixing the mistake in Macedonian treebank (mk_mtb-ud-test.conllu), in sent_id=other0010, there is personal pronoun 'ми' marked as expl:pv, it should be iobj
		if node.deprel == 'expl:pv' and node.lemma == 'ми' and node.feats['PronType'] == 'Prs':
			node.deprel = ''
			node.udeprel = 'iobj'

		# in Old Church Slavonic, there is feature Mood=Sub, but this is a notation for conditional mood
		if node.feats['Mood'] == 'Sub':
			node.feats['Mood'] = 'Cnd'

		# TODO maybe we want to set Tense=Fut for the perfective verbs with Tense=Pres? This could solve the problem with the simplified detection of the future tense in Czech
		# but there are many verbs with no Aspect value, so the problem is still there 



		
				
