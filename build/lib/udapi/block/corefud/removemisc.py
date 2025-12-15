from udapi.core.block import Block
import re

class RemoveMisc(Block):
    """Deleting all temporary attributes after primary conversions"""

    def __init__(self, attrnames='', **kwargs):
        """ Arg: attrnames = comma-separated list of Misc attributes to be deleted"""
        super().__init__(**kwargs)
        self.attrs4deletion = set(attrnames.split(','))
    
    def process_tree(self,root):
        for node in root.descendants_and_empty:
            for attrname in list(node.misc):
                shortattrname = re.sub(r'\[\d+\]',r'',attrname)
                if shortattrname in self.attrs4deletion:
                    del node.misc[attrname]

