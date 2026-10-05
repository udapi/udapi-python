"""
Block ud.FixOblToNmod will change the dependency relation from obl to nmod
if the parent clearly does not head a clause. It fixes the validation error
of the type obl-should-be-nmod.
"""
from udapi.core.block import Block
import re


class FixOblToNmod(Block):
    """
    Make sure obl is not used when a nominal modifies another nominal.
    """

    def process_node(self, node):
        if node.udeprel == 'obl':
            # obl can modify adjectives and adverbs even if they do not head a clause.
            # Focus on nominal heads only. That is what validator does, too.
            if node.parent.upos in ['NOUN', 'PROPN', 'PRON']:
                # Even with these parent parts of speech the parent can head
                # a clause and then an obl dependent may be legitimate. Focus
                # on parent deprels that clearly indicate it is not a clause.
                if node.parent.udeprel in ['nsubj', 'obj', 'iobj', 'obl', 'vocative', 'dislocated', 'expl', 'nmod']:
                    node.deprel = self.get_new_deprel(node.deprel, node.upos)
                    # If there are enhanced dependencies, we must fix them, too.
                    for hd in node.deps:
                        fixed_edeprel = self.get_new_deprel(hd['deprel'], node.upos)
                        if fixed_edeprel != hd['deprel']:
                            hd['deprel'] = fixed_edeprel

    def get_new_deprel(self, old_deprel, upos):
        """
        Changes obl to nmod. If there are subtypes, preserves them.
        """
        if old_deprel == 'obl':
            # Some dependent UPOS should be neither obl nor nmod.
            if upos == 'ADV':
                return 'advmod'
            elif upos == 'VERB':
                return 'advcl'
            else:
                return 'nmod'
        elif re.match(r'obl:', old_deprel):
            # Some dependent UPOS should be neither obl nor nmod.
            if upos == 'ADV':
                return 'advmod'
            elif upos == 'VERB':
                return 'advcl'
            else:
                # Discard certain subtypes while keeping others.
                ###!!! This should be customizable! discard_subtypes=agent,subj
                new_deprel = re.sub(r':(agent|arg):', ':', old_deprel)
                new_deprel = re.sub(r':(agent|arg)$', '', new_deprel)
                return re.sub(r'^obl', 'nmod', new_deprel)
        else:
            return old_deprel
