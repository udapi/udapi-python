"""
Block ud.FixMultiObjects will ensure that no node has more than one (direct) object child.
"""
from udapi.core.block import Block


class FixMultiObjects(Block):
    """
    Make sure there is at most one object.
    """

    def process_node(self, node):
        objects = [x for x in node.children if x.udeprel == 'obj']
        # For the moment, we take the dummiest approach possible: The first object survives and all others are forced to a different deprel.
        if len(objects) > 1:
            objects = objects[1:]
            for o in objects:
                o.deprel = 'iobj'
