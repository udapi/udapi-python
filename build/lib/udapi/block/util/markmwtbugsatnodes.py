"""util.MarkMwtBugsAtNodes copies Bug attributes from MISC of multiword tokens to MISC of member nodes.
   Otherwise they will be ignored when write.TextModeTrees marked_only=1 is called."""

from udapi.core.block import Block

class MarkMwtBugsAtNodes(Block):
    """
    If a node belongs to a multiword token and the MWT has Bug in MISC, copy
    the Bug to the node so that filtering trees with bugs works.
    The same bug note will be copied to all nodes in the MWT.
    """

    ###!!! Do we want to do the same thing also with ToDo attributes?
    def bug(self, node, bugstring):
        bugs = []
        if node.misc['Bug']:
            bugs = node.misc['Bug'].split('+')
        if not bugstring in bugs:
            bugs.append(bugstring)
        node.misc['Bug'] = '+'.join(bugs)

    def process_node(self, node):
        if node.multiword_token:
            if node.multiword_token.misc['Bug']:
                self.bug(node, node.multiword_token.misc['Bug'])
