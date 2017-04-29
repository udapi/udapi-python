"""Block ud.FixPunct for making sure punctuation is attached projectively.

Punctuation in Universal Dependencies has the tag PUNCT, dependency relation punct,
and is always attached projectively, usually to the head of a neighboring subtree
to its left or right.
Punctuation normally does not have children. If it does, we will skip it.
It is unclear what to do anyway, and we won't have to check for cycles.

Tries to re-attach punctuation projectively.
It should help in cases where punctuation is attached randomly, always to the root
or always to the neighboring word. However, there are limits to what it can do;
for example it cannot always recognize whether a comma is introduced to separate
the block to its left or to its right. Hence if the punctuation before running
this block is almost good, the block may actually do more harm than good.

Since the punctuation should not have children, we should not create a non-projectivity
if we check the roof edges going to the right.
However, it is still possible that we will attach the punctuation non-projectively
by joining a non-projectivity that already exists.
For example, the left neighbor (node i-1) may have its parent at i-3,
and the node i-2 forms a gap (does not depend on i-3).
"""
from udapi.core.block import Block
# pylint: disable=no-self-use

# TODO Add a heuristics for ASCI "quotes".
# TODO Add ‘single’ quotes, but make sure these symbols are not used e.g. as apostrophes.
# TODO We need to know the language, there are many other quotation styles,
#      e.g. Finnish and Swedish uses the same symbol for opening and closing: ”X”.
#      Danish uses uses the French quotes, but switched: »X«.
PAIRED_PUNCT = {
    '(': ')',
    '[': ']',
    '{': '}',
    '“': '”',   # quotation marks used in English,...
    '„': '“',   # Czech, German, Russian,...
    '«': '»',   # French, Russian, Spanish,...
    '‹': '›',   # dtto
    '《': '》',  # Korean, Chinese
    '「': '」',  # Chinese, Japanese
    '『': '』',  # dtto
    }


class FixPunct(Block):
    """Make sure punct nodes are attached punctuation is attached projectively."""

    def process_tree(self, root):
        # First, make sure no PUNCT has children
        for node in root.descendants:
            while node.parent.upos == "PUNCT":
                node.parent = node.parent.parent

        # Then make sure subordinate punctuations have correct parent.
        for node in root.descendants:
            if node.upos == "PUNCT" and not PAIRED_PUNCT.get(node.form, None):
                self._fix_subord_punct(node)

        # Then fix paired punctuations: quotes and brackets.
        for node in root.descendants:
            closing_punct = PAIRED_PUNCT.get(node.form, None)
            if closing_punct is not None:
                self._fix_paired_punct(root, node, closing_punct)

    def _fix_subord_punct(self, node):
        # Initialize the candidates (left and right) with the nearest nodes excluding punctuation.
        l_cand, r_cand = node.prev_node, node.next_node
        while l_cand.ord > 0 and l_cand.upos == "PUNCT":
            l_cand = l_cand.prev_node
        while r_cand is not None and r_cand.upos == "PUNCT":
            r_cand = r_cand.next_node

        # Climb up from the candidates, until we would reach the root or "cross" the punctuation.
        if l_cand.is_root():
            l_cand = None
        else:
            while not l_cand.parent.is_root() and l_cand.parent.precedes(node):
                l_cand = l_cand.parent
        if r_cand is not None:
            while not r_cand.parent.is_root() and node.precedes(r_cand.parent):
                r_cand = r_cand.parent

        # Now select between l_cand and r_cand -- which will be the new parent?
        # The lower one. Note that one if neither is descendant of the other and neither is None
        # (which can happen in rare non-projective cases), we arbitrarily prefer r_cand.
        if l_cand is not None and not l_cand.is_root() and l_cand.is_descendant_of(r_cand):
            node.parent = l_cand
            node.deprel = "punct"
        elif r_cand is not None:
            node.parent = r_cand
            node.deprel = "punct"

    def _fix_paired_punct(self, root, opening_node, closing_punct):
        nested_level = 0
        for node in root.descendants[opening_node.ord:]:
            if node.form == opening_node.form:
                nested_level += 1
            elif node.form == closing_punct:
                if nested_level > 0:
                    nested_level -= 0
                else:
                    self._fix_pair(root, opening_node, node)
                    return

    def _fix_pair(self, root, opening_node, closing_node):
        heads = []
        for node in root.descendants[opening_node.ord: closing_node.ord - 1]:
            if node.parent.precedes(opening_node) or closing_node.precedes(node.parent):
                if node.upos != 'PUNCT':
                    heads.append(node)
        if len(heads) == 1:
            opening_node.parent = heads[0]
            closing_node.parent = heads[0]
        elif len(heads) > 1:
            opening_node.parent = sorted(heads, key=lambda n: n.descendants(add_self=1)[0].ord)[0]
            closing_node.parent = sorted(heads, key=lambda n: -n.descendants(add_self=1)[-1].ord)[0]
