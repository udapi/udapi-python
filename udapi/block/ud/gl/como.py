"""
Block ud.gl.Prep tries to solve some errors in Galician CTG where
the conjunction "como" is mistakenly attached as a sibling of its phrase.

Author: Dan Zeman
"""
from udapi.core.block import Block

class Como(Block):
    """Block for fixing "como" in UD_Galician-CTG."""

    def process_node(self, node):
        if node.form == 'como':
            # This part is problematic and there are many counterexamples, so
            # I am disabling it after I did the initial run.
            if False:
                rightsiblings = node.siblings(following_only=True)
                if len(rightsiblings) > 0:
                    if node.parent.ord < node.ord or node.parent.ord > rightsiblings[0].ord:
                        node.parent = rightsiblings[0]
                        # The conjunction is often mistagged as pronoun but we will not attempt to fix that now.
                        node.deprel = 'mark' if node.upos == 'SCONJ' else 'nmod'
            # Regardless whether "como" was already attached to the following
            # phrase or we had to re-attach it, make sure that the phrase is
            # not treated as a core argument.
            if node.parent.ord > node.ord and node.parent.udeprel in ['nsubj', 'obj', 'iobj', 'csubj', 'ccomp']:
                node.parent.deprel = 'advcl'
