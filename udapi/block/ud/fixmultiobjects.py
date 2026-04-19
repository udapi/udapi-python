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
        if len(objects) > 1:
            subjects = [x for x in node.children if x.udeprel in ['nsubj', 'csubj']]
            # Some heuristics that could work in AnCora:
            # If all objects are after the verb, keep the one that is closest to the verb.
            if objects[0].ord > node.ord:
                objects = objects[1:]
                for o in objects:
                    o.deprel = 'obl:arg'
                    o.deps[0]['deprel'] = 'obl:arg'
            elif objects[-1].ord < node.ord:
                objects = objects[:-1]
                for o in objects:
                    o.deprel = 'dislocated'
                    o.deps[0]['deprel'] = 'dislocated'
            # ho experimenta tot
            elif objects[-1].lemma in ['tot', 'todo']:
                objects[-1].parent = objects[0]
                objects[-1].deprel = 'nmod'
                objects[-1].deps[0]['parent'] = objects[0]
                objects[-1].deps[0]['deprel'] = 'nmod'
            # X se llama Y
            elif node.lemma in ['llamar', 'considerar', 'decir', 'denunciar', 'causar', 'escribir', 'hacer', 'rubricar']:
                objects[-1].deprel = 'xcomp'
                objects[-1].deps[0]['deprel'] = 'xcomp'
            elif len(subjects) == 0:
                objects[0].deprel = 'nsubj'
                objects[0].deps[0]['deprel'] = 'nsubj'
            else:
                objects[0].deprel = 'dislocated'
                objects[0].deps[0]['deprel'] = 'dislocated'
            # For the moment, we take the dummiest approach possible: The first object survives and all others are forced to a different deprel.
            #objects = objects[1:]
            #for o in objects:
            #    o.deprel = 'iobj'
