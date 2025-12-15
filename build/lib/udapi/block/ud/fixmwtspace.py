"""
Block ud.FixMwtSpace looks for multiword tokens whose form contains a space,
which should be avoided. If found, the block checks whether it can remove
the multiword token seamlessly, that is, whether the syntactic words correspond
to the space-delimited parts of the multiword token. If possible, the MWT
line will be removed.
"""
from udapi.core.block import Block
import re


class FixMwtSpace(Block):
    """Try to remove multiword tokens with spaces."""

    def process_node(self, node):
        if node.multiword_token:
            mwt = node.multiword_token
            if re.search(r' ', mwt.form):
                if node == mwt.words[0]:
                    wordforms = [x.form for x in mwt.words]
                    if ' '.join(wordforms) == mwt.form:
                        mwt.remove()
