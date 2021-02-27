from udapi.core.block import Block
from collections import Counter
import re

class BridgingClusters(Block):

    def process_node(self,node):

        if 'Bridging' in node.misc and "+" in node.misc['BridgingAllTargetClusterTexts']:
            print("SENTENCE      : "+node.root.get_sentence())
            print("SOURCE MENTION: "+node.misc['MentionText'])
            print("RELATION:       "+node.misc['Bridging'])
            print("TARGET MENTION: "+node.misc['BridgingTargetMentionText'])
            print("TARGET CLUSTER: "+node.misc['BridgingAllTargetClusterTexts'])
            print()


