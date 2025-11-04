"""Block ud.JoinAsMwt for creating multi-word tokens

if multiple neighboring words are not separated by a space
and the boundaries between the word forms are alphabetical.
"""
from udapi.core.block import Block


class JoinAsMwt(Block):
    """Create MWTs if words are not separated by a space.."""

    def __init__(self, revert_orig_form=True, **kwargs):
        """Args:
        revert_orig_form: if any node of the newly created MWT has `misc['OrigForm']`,
            it is used as the FORM (and deleted from MISC). Useful after `ud.ComplyWithText`.
            Default=True.
        """
        super().__init__(**kwargs)
        self.revert_orig_form = revert_orig_form

    def process_node(self, node):
        if node.multiword_token:
            return
        mwt_nodes = [node]
        while (node.next_node and not node.next_node.multiword_token
               and self.should_join(node, node.next_node)):
            node = node.next_node
            mwt_nodes.append(node)
        if len(mwt_nodes) > 1:
            self.create_mwt(mwt_nodes)

    def should_join(self, node, next_node):
        return node.no_space_after and node.form[-1].isalpha() and next_node.form[0].isalpha()

    def create_mwt(self, mwt_nodes):
        mwt_form = ''.join([n.form for n in mwt_nodes])
        mwt = mwt_nodes[0].root.create_multiword_token(words=mwt_nodes, form=mwt_form)
        if mwt_nodes[0].node.misc['SpaceAfter'] == 'No':
            mwt.misc['SpaceAfter'] = 'No'
        for mwt_node in mwt_nodes:
            del mwt_node.misc['SpaceAfter']
        if self.revert_orig_form:
            for mwt_node in mwt_nodes:
                if mwt_node.misc['OrigForm']:
                    mwt_node.form = mwt_node.misc['OrigForm']
                    del mwt_node.misc['OrigForm']
        self.postprocess_mwt()

    # a helper method to be overriden
    def postprocess_mwt(self, mwt):
        pass
