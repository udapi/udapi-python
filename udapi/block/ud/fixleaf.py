"""
Block ud.FixLeaf checks that function word dependents are leaves.
Certain known exceptions are observed (e.g., fixed expressions).
"""
from udapi.core.block import Block
import logging
import re

class FixLeaf(Block):
    """
    Make sure that aux and cop dependents are leaves unless one of the known
    exceptions applies.
    """

    def __init__(self, deprels='aux,cop,cc', **kwargs):
        """
        Args:
        deprels: comma-separated list of deprels to be fixed. Default = aux,cop,case,mark,cc.
        """
        super().__init__(**kwargs)
        self.deprels = deprels.split(',')

    def process_node(self, node):
        for deprel in self.deprels:
            if node.udeprel == deprel:
                # Every function dependent can have a fixed child.
                # We will also allow conj, cc, punct, goeswith, reparandum.
                allowed = ['fixed', 'punct', 'goeswith', 'reparandum']
                if deprel != 'cc':
                    allowed += ['conj', 'cc']
                children = [c for c in node.children if not (c.udeprel in allowed)]
                # Re-attach the remaining children to an acceptable ancestor.
                ancestor = node.parent
                while ancestor.udeprel in self.deprels:
                    ancestor = ancestor.parent
                for c in children:
                    c.parent = ancestor
                    # If there are enhanced dependencies, check whether we want to redirect them too.
                    if c.deps:
                        for edep in c.deps:
                            if edep['parent'] == node:
                                edep['parent'] = ancestor
