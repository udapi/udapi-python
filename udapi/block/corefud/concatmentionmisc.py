from udapi.core.block import Block
from collections import Counter
import re

class ConcatMentionMisc(Block):
    """All MISC attributes named MentionMisc_... are concatenated into MentionMisc"""

    def process_tree(self,root):
        for node in root.descendants_and_empty:
            for attrname in list(node.misc):
                matchObj = re.match('MentionMisc_([^[]+)((\[\d+\])?)',attrname)
                if matchObj:
                    innerattrib = matchObj.group(1)
                    index = matchObj.group(2)

                    finalattr = 'MentionMisc'+index
                    value = node.misc[attrname]
                
                    if finalattr not in node.misc:
                        node.misc[finalattr] = f'{innerattrib}:{value}'
                    else:
                        node.misc[finalattr] += f' {innerattrib}:{value}'
                    del node.misc[attrname]

