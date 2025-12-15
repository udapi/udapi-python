"""
Block ud.FixMultiSubjects will ensure that no node has more than one subject child (except those
marked as :outer).
"""
import re
from udapi.core.block import Block


class FixMultiSubjects(Block):
    """
    Make sure there is at most one subject that is not marked as :outer.
    """

    def process_node(self, node):
        subjects = [x for x in node.children if re.match(r"^[nc]subj(:|$)", x.deprel) and not re.search(r":outer$", x.deprel)]
        # For the moment, we take the dummiest approach possible: The first subject survives and all others are forced to a different deprel.
        if len(subjects) > 1:
            subjects = subjects[1:]
            for s in subjects:
                if re.match(r"^n", s.deprel):
                    s.deprel = 'obl'
                else:
                    s.deprel = 'advcl'
