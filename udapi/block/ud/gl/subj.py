"""
Block ud.gl.Subj tries to solve some errors in Galician CTG that result in the
too-many-subjects validation error.

Author: Dan Zeman
"""
from udapi.core.block import Block
import regex as re

class Subj(Block):
    """Block for fixing too-many-subjects in UD_Galician-CTG."""

    def process_node(self, node):
        subjects = [x for x in node.children if x.udeprel in ['nsubj', 'csubj'] and not re.search(r':outer$', x.deprel)]
        # Certain lemmas are unlikely to be subjects ("onde"), others could be
        # subjects in theory but were seen in the treebank only in clearly non
        # subject positions (while mistakenly tagged "nsubj").
        if len(subjects) > 1:
            for x in subjects:
                if re.fullmatch(r'(canto|como|dous|em|lle|miúdo|obstante|obter|onde|pena|principio|respecto|seis|tarde|través|tres)', x.lemma):
                    x.deprel = 'obl' if node.upos in ['VERB', 'ADJ', 'ADV'] else 'nmod'
                elif x.lemma == 'que' and x.prev_node and re.fullmatch(r'(dado|xa)', x.prev_node.form.lower()):
                    x.upos = 'SCONJ'
                    x.xpos = 'CS'
                    x.feats['PronType'] = ''
                    x.deprel = 'mark'
                    if not x.prev_node.is_descendant_of(x) and not x.is_descendant_of(x.prev_node):
                        x.prev_node.parent = node
            subjects = [x for x in node.children if x.udeprel in ['nsubj', 'csubj'] and not re.search(r':outer$', x.deprel)]
        if len(subjects) > 1:
            ques = [x for x in node.children if x.ord > subjects[0].ord and x.ord < node.ord and x.lemma in ['que', 'qual']]
            cops = [x for x in node.children if x.ord > subjects[0].ord and x.ord < node.ord and x.udeprel == 'cop']
            # Mis-annotated relative clause where the antecedent is treated as a subject of the relative clause.
            # *As situacións* ... en as que *as perosas* viven ...
            # Avoid situations where there is also a copula in between:
            # El obxetivo es que ...
            if subjects[0].ord < node.ord and len(ques) > 0 and len(cops) == 0:
                # Make the current node dependent on the antecedent.
                antecedent = subjects[0]
                antecedent.parent = node.parent
                antecedent.deprel = node.deprel
                node.parent = antecedent
                node.deprel = 'acl:relcl'
            # *que* sufrimos maior discriminación ...
            # If "que" is a subject, its verb is typically in third person, so here it is likely that "que" is just a subordinator.
            elif subjects[0].lemma == 'que' and re.match(r'VM..[12]', node.xpos):
                subjects[0].upos = 'SCONJ'
                subjects[0].xpos = 'CS'
                subjects[0].feats['PronType'] = ''
                subjects[0].deprel = 'mark'
            # Some verbs resemble pseudo-copulas and their second "subject"
            # could be a secondary predicate.
            elif len(subjects) == 2 and re.fullmatch(r'(aparecer|considerar|definir|empregar|estar|interpretar|parecer|referir|ser|servir|significar|valorar)', node.lemma):
                subjects[1].deprel = 'xcomp'
            # With a copula, we may be actually observing the outer subject.
            # Note that we defined the cops list as copulas between the first subject and the current node (verb).
            # This will work for the example I observed (outer subject, copula, inner subject, verb) but it may miss other examples.
            elif len(subjects) == 2 and len(cops) > 0:
                subjects[0].deprel = 'csubj:outer' if subjects[0].upos == 'VERB' else 'nsubj:outer'
