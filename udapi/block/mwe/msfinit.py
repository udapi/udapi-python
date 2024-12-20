"""
Morphosyntactic features (UniDive):
Initialization. Copies features from FEATS as MSF* attributes to MISC.
"""
from udapi.core.block import Block

class MsfInit(Block):


    def process_node(self, node):
        """
        For every feature in FEATS, creates its MSF* counterpart in MISC.
        """
        for f in node.feats:
            node.misc['MSF'+f] = node.feats[f]
