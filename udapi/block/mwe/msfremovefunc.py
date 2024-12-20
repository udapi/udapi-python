"""
Morphosyntactic features (UniDive):
Cleanup. Removes MSF* features from MISC for function nodes (MSFFunc=Yes).
"""
from udapi.core.block import Block

class MsfRemoveFunc(Block):


    def process_node(self, node):
        """
        Removes MSF* features if MSFFunc=Yes.
        """
        if node.misc['MSFFunc'] == 'Yes':
            for msf in node.misc:
                if msf.startswith('MSF'):
                    node.misc[msf] = ''
