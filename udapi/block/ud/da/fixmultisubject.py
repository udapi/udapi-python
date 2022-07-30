"""
Block ud.da.FixMultiSubject tries to fix some systemic instances of predicates
that have more than one subject dependent.
"""
from udapi.core.block import Block
import re

class FixMultiSubject(Block):
    """
    Make sure that a predicate has at most one subject. Note that it can
    only fix instances that follow certain pattern observed in the Danish
    data.
    """

    def process_node(self, node):
        subjects = [x for x in node.children if re.match(r'^[nc]subj$', x.udeprel)]
        if len(subjects) > 1:
            # Pattern 1: A node is is attached as xcomp to the current node, and
            # one of the subjects is closer to that xcomp than to the current
            # node.
            xcompchildren = [x for x in node.children if x.udeprel == 'xcomp']
            # Pattern 2: Similar to pattern 1, but advcl instead of xcomp, and
            # possibly not so many other mis-attached dependents.
            advclchildren = [x for x in node.children if x.udeprel == 'advcl']
            # Pattern 3: Instead of xcomp or advcl, there is a simple amod
            # (under a verb!), in fact an adjective with a copula that should
            # have been advcl.
            amodchildren = [x for x in node.children if x.udeprel == 'amod']
            if len(subjects) == 2 and len(xcompchildren) > 0:
                for xcompnode in xcompchildren:
                    dn = [dist(node, x) for x in subjects]
                    dx = [dist(xcompnode, x) for x in subjects]
                    # Is the first subject closer to xcomp than it is to the current node?
                    # At the same time, is the second subject closer to the current node than it is to xcomp?
                    if dx[0] <= dn[0] and dn[1] <= dx[1]:
                        # The first subject should be re-attached to the xcomp node.
                        subjects[0].parent = xcompnode
                        # There are typically other dependents that should belong to the xcomp node.
                        for c in node.children:
                            if c != xcompnode and dist(xcompnode, c) < dist(node, c):
                                c.parent = xcompnode
                        # The xcompnode should probably be attached as something else
                        # than xcomp, perhaps even the direction of the relation should
                        # be reversed, but one would have to resolve this manually.
                        xcompnode.misc['ToDo'] = 'check-xcomp'
                        break
                    # Is the second subject closer to xcomp than it is to the current node?
                    # At the same time, is the first subject closer to the current node than it is to xcomp?
                    elif dx[1] <= dn[1] and dn[0] <= dx[0]:
                        # The second subject should be re-attached to the xcomp node.
                        subjects[1].parent = xcompnode
                        # There are typically other dependents that should belong to the xcomp node.
                        for c in node.children:
                            if c != xcompnode and dist(xcompnode, c) < dist(node, c):
                                c.parent = xcompnode
                        # The xcompnode should probably be attached as something else
                        # than xcomp, perhaps even the direction of the relation should
                        # be reversed, but one would have to resolve this manually.
                        xcompnode.misc['ToDo'] = 'check-xcomp'
                        break
            elif len(subjects) == 2 and len(advclchildren) > 0:
                for advclnode in advclchildren:
                    dn = [dist(node, x) for x in subjects]
                    dx = [dist(advclnode, x) for x in subjects]
                    # Is the first subject closer to advcl than it is to the current node?
                    # At the same time, is the second subject closer to the current node than it is to advcl?
                    if dx[0] < dn[0] and dn[1] < dx[1]:
                        # The first subject should be re-attached to the advcl node.
                        subjects[0].parent = advclnode
                        break
                    # Is the second subject closer to advcl than it is to the current node?
                    # At the same time, is the first subject closer to the current node than it is to advcl?
                    elif dx[1] < dn[1] and dn[0] < dx[0]:
                        # The second subject should be re-attached to the xcomp node.
                        subjects[1].parent = advclnode
                        break
            elif len(subjects) == 2 and len(amodchildren) > 0:
                for amodnode in amodchildren:
                    dn = [dist(node, x) for x in subjects]
                    dx = [dist(amodnode, x) for x in subjects]
                    # Is the first subject closer to amod than it is to the current node?
                    # At the same time, is the second subject closer to the current node than it is to amod?
                    if dx[0] < dn[0] and dn[1] < dx[1]:
                        # The first subject should be re-attached to the advcl node.
                        subjects[0].parent = amodnode
                        amodnode.deprel = 'advcl'
                        # There are typically other dependents that should belong to the amod node.
                        for c in node.children:
                            if c != amodnode and dist(amodnode, c) < dist(node, c):
                                c.parent = amodnode
                        break
                    # Is the second subject closer to amod than it is to the current node?
                    # At the same time, is the first subject closer to the current node than it is to amod?
                    elif dx[1] < dn[1] and dn[0] < dx[0]:
                        # The second subject should be re-attached to the xcomp node.
                        subjects[1].parent = amodnode
                        amodnode.deprel = 'advcl'
                        # There are typically other dependents that should belong to the amod node.
                        for c in node.children:
                            if c != amodnode and dist(amodnode, c) < dist(node, c):
                                c.parent = amodnode
                        break

def dist(x, y):
    if x.ord < y.ord:
        a = x
        b = y
    else:
        a = y
        b = x
    d = b.ord - a.ord
    # Count the commas between the two nodes. A comma should be seen as increasing
    # the distance of the nodes, that is, decreasing the probability that they
    # are in the same clause.
    nc = 0
    for i in a.root.descendants:
        if i.ord > a.ord and i.ord < b.ord:
            if i.form == ',':
                nc += 1
    d += nc * 10
    return d
