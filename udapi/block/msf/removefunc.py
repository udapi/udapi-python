"""
Morphosyntactic features (UniDive):
Cleanup. Removes MSF* features from MISC for function nodes (MSFFunc=Yes).
"""
from udapi.core.block import Block

class RemoveFunc(Block):


    def process_node(self, node):
        """
        Removes MSF* features if MSFFunc=Yes.
        """
        if node.misc['MSFFunc'] == 'Yes':
            msfeats = [x for x in node.misc if x.startswith('MSF')]
            for msf in msfeats:
                node.misc[msf] = ''
