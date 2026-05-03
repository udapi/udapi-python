"""
Block ud.gl.SubClause tries to solve some errors in Galician CTG where
a subordinate clause is mistakenly merged with the superordinate clause.

Author: Dan Zeman
"""
from udapi.core.block import Block

class SubClause(Block):
    """Block for fixing subordinate clauses in UD_Galician-CTG."""

    def process_node(self, node):
        # If the current node is a verb, it has no children and it follows
        # both its parent verb and a sibling subordinator, it should form
        # a subordinate clause together with some of its siblings.
        if node.upos == 'VERB' and len(node.children) == 0 and node.parent.ord < node.ord:
            focus = [x for x in node.siblings if x.ord > node.parent.ord and x.ord < node.ord]
            if len([x for x in focus if x.udeprel == 'mark']) > 0:
                # Re-attach the subordinator and subsequent siblings to me.
                active = False
                for i in range(len(focus)):
                    x = focus[i]
                    if not active and x.udeprel == 'mark':
                        active = True
                        if x.lemma == 'que' and i > 0 and focus[i-1].lemma in [',', 'xa']:
                            focus[i-1].parent = node
                    if active:
                        x.parent = node
                # Re-attach all siblings after me to me.
                for x in node.siblings:
                    if x.ord > node.ord:
                        x.parent = node
