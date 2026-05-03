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
