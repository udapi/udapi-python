"""
Block ud.gl.DeQue tries to solve some errors in Galician CTG where
a subordinate clause starts with preposition + "que", the preposition is not
(but should be) attached to "que", and "que" is (but should not be) annotated
as a core argument.

Author: Dan Zeman
"""
from udapi.core.block import Block

class DeQue(Block):
    """Block for fixing "de que" clauses in UD_Galician-CTG."""

    def process_node(self, node):
        # Is the current node "que" and is it preceded by a preposition?
        if not node.prev_node:
            return
        # Originally I thought we would catch any "que" even if currently tagged 'SCONJ' (it could be annotation error).
        # However, it turns out some of them may be correct, e.g., compound marker "salvo que" ("salvo" is 'ADP').
        # So I am now requiring that "que" is already pronoun.
        if node.lemma == 'que' and node.upos == 'PRON' and node.prev_node.upos == 'ADP':
            que = node
            preposition = node.prev_node
            # I have not seen it but que could be attached as a descendant of the preposition.
            if que.is_descendant_of(preposition):
                que.parent = preposition.parent
            que.deprel = 'obl' if que.parent.upos in ['VERB', 'ADJ', 'ADV'] else 'nmod'
            if que.upos == 'SCONJ':
                que.upos = 'PRON'
                que.xpos = 'PR0CN000'
                que.feats['PronType'] = 'Rel'
            preposition.parent = que
            preposition.deprel = 'case'
            # I do not expect the preposition to have children but if it does, reattach them to que.
            for x in preposition.children:
                x.parent = que
