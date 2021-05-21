"""Block ud.FixPunct for making sure punctuation is attached projectively.

Punctuation in Universal Dependencies has the tag PUNCT, dependency relation punct,
and is always attached projectively, usually to the head of a neighboring subtree
to its left or right (see https://universaldependencies.org/u/dep/punct.html).
Punctuation normally does not have children. If it does, we will fix it first.

This block tries to re-attach punctuation projectively and according to the guidelines.
It should help in cases where punctuation is attached randomly, always to the root
or always to the neighboring word. However, there are limits to what it can do;
for example it cannot always recognize whether a comma is introduced to separate
the block to its left or to its right. Hence if the punctuation before running
this block is almost good, the block may actually do more harm than good.

Since the punctuation should not have children, we should not create a non-projectivity
if we check the root edges going to the right.
"""
from udapi.core.block import Block
# pylint: disable=no-self-use

# TODO We need to know the language, there are many other quotation styles,
#      e.g. Finnish and Swedish uses the same symbol for opening and closing: ”X”.
#      Danish uses uses the French quotes, but switched: »X«.
PAIRED_PUNCT = {
    '(': ')',
    '[': ']',
    '{': '}',
    '"': '"',   # ASCII double quotes
    "'": "'",   # ASCII single quotes
    '“': '”',   # quotation marks used in English,...
    '„': '“',   # Czech, German, Russian,...
    '«': '»',   # French, Russian, Spanish,...
    '‹': '›',   # dtto
    '《': '》',  # Korean, Chinese
    '「': '」',  # Chinese, Japanese
    '『': '』',  # dtto
    '¿': '?',   # Spanish question quotation marks
    '¡': '!',   # Spanish exclamation quotation marks
    }

FINAL_PUNCT = '.?!'


class FixPunct(Block):
    """Make sure punctuation nodes are attached projectively."""

    def __init__(self, check_paired_punct_upos=False, copy_to_enhanced=False, **kwargs):
        """Create the ud.FixPunct block instance.

        Args:
        check_paired_punct_upos: fix paired punctuation tokens only if their UPOS=PUNCT.
            The default is false, which means that fixed punctuation is detected only
            based on the form with the exception of single quote / apostrophe character,
            which is frequently ambiguous, so UPOS=PUNCT is checked always.
        copy_to_enhanced: for all PUNCT nodes, let the enhanced depencies be the same
            as the basic dependencies.
        """
        super().__init__(**kwargs)
        self._punct_type = None
        self.check_paired_punct_upos = check_paired_punct_upos
        self.copy_to_enhanced = copy_to_enhanced

    def process_tree(self, root):
        # First, make sure no PUNCT has children.
        # This may introduce multiple subroots, which will be fixed later on
        # (preventing to temporarily create multiple subroots here would prevent fixing some errors).
        for node in root.descendants:
            while node.parent.upos == "PUNCT":
                node.parent = node.parent.parent

        # Second, fix paired punctuations: quotes and brackets, marking them in _punct_type.
        # This should be done before handling the subordinate punctuation,
        # in order to prevent non-projectivities e.g. in dot-before-closing-quote style sentences:
        #   I call him "Bob."
        # Here both quotes and the sentence-final dot should be attached to "Bob".
        # (As you can see on the previous line, I don't like this American typographic rule.)
        self._punct_type = [None] * (1 + len(root.descendants))
        for node in root.descendants:
            if self._punct_type[node.ord] != 'closing':
                closing_punct = PAIRED_PUNCT.get(node.form, None)
                if closing_punct is not None:
                    self._fix_paired_punct(root, node, closing_punct)

        # Third, fix subordinate punctuation (i.e. any punctuation not marked in _punct_type).
        for node in root.descendants:
            if node.upos == "PUNCT" and not self._punct_type[node.ord]:
                self._fix_subord_punct(node)


        # UD requires "exactly one word is the head of the sentence, dependent on a notional ROOT", i.e. a single "subroot".
        # This seems to be a stronger rule than no-PUNCT-children because it is checked by the validator.
        # So lets prevent multiple subroots (at the cost of possibly re-introducing PUNCT-children).
        if len(root.children) > 1:
            selected_subroot = next((n for n in root.children if n.udeprel == 'root'), root.children[0])
            for a_subroot in root.children:
                if a_subroot != selected_subroot:
                    a_subroot.parent = selected_subroot

        # Check if the subroot is still marked with deprel=root.
        # This may not hold if the original subroot was a paired punctuation, which was rehanged.
        if root.children[0].udeprel != 'root':
            root.children[0].udeprel = 'root'
            for another_node in root.children[0].descendants:
                if another_node.udeprel == 'root':
                    another_node.udeprel = 'punct'

        # TODO: This block changes parents not only for PUNCT nodes. These should be reflected into enhanced deps as well.
        if self.copy_to_enhanced:
            for node in root.descendants:
                if node.upos == "PUNCT":
                    node.deps = [{'parent': node.parent, 'deprel': 'punct'}]

    def _fix_subord_punct(self, node):
        # Dot used as the ordinal-number marker (in some languages) or abbreviation marker.
        # TODO: detect these cases somehow
        # Numbers can be detected with `node.parent.form.isdigit()`,
        # but abbreviations are more tricky because the Abbr=Yes feature is not always used.
        if node.form == '.' and node.parent == node.prev_node:
            return

        # Even non-paired punctuation like commas and dashes may work as paired.
        # Detect such cases and try to preserve, but only if projective.
        p_desc = node.parent.descendants(add_self=1)
        if node in (p_desc[0], p_desc[-1]) and len(p_desc) == p_desc[-1].ord - p_desc[0].ord + 1:
            if (p_desc[0].upos == 'PUNCT' and p_desc[-1].upos == 'PUNCT'
                    and p_desc[0].parent == node.parent and p_desc[-1].parent == node.parent):
                return

        # Initialize the candidates (left and right) with the nearest nodes excluding punctuation.
        # Final punctuation should not be attached to any following, so exclude r_cand there.
        l_cand, r_cand = node.prev_node, node.next_node
        if node.form in FINAL_PUNCT:
            r_cand = None
        while l_cand.ord > 0 and l_cand.upos == "PUNCT":
            if self._punct_type[l_cand.ord] == 'opening' and l_cand.parent != node:
                l_cand = None
                break
            l_cand = l_cand.prev_node
        while r_cand is not None and r_cand.upos == "PUNCT":
            if self._punct_type[r_cand.ord] == 'closing' and r_cand.parent != node:
                r_cand = None
                break
            r_cand = r_cand.next_node

        # Climb up from the candidates, until we would reach the root or "cross" the punctuation.
        # If the candidates' descendants span across the punctuation, we also stop
        # because climbing higher would cause a non-projectivity (the punct would be the gap).
        l_path, r_path = [l_cand], [r_cand]
        if l_cand is None or l_cand.is_root():
            l_cand, l_path = None, []
        else:
            while (not l_cand.parent.is_root() and l_cand.parent.precedes(node)
                   and not node.precedes(l_cand.descendants(add_self=1)[-1])):
                l_cand = l_cand.parent
                l_path.append(l_cand)
        if r_cand is not None:
            while (not r_cand.parent.is_root() and node.precedes(r_cand.parent)
                   and not r_cand.descendants(add_self=1)[0].precedes(node)):
                r_cand = r_cand.parent
                r_path.append(r_cand)

        # Filter out candidates which would lead to non-projectivities, i.e. bugs
        # punct-nonproj and punct-nonproj-gap as checked by the UD validator and ud.MarkBugs.
        orig_parent = node.parent
        l_path = [n for n in l_path if n and self._will_be_projective(node, n)]
        r_path = [n for n in r_path if n and self._will_be_projective(node, n)]
        l_cand = l_path[-1] if l_path else None
        r_cand = r_path[-1] if r_path else None
        node.parent = orig_parent

        # Now select between l_cand and r_cand -- which will be the new parent?
        # The lower one. Note that if neither is descendant of the other and neither is None
        # (which can happen in rare non-projective cases), we arbitrarily prefer l_cand,
        # but if the original parent is either on l_path or r_path, we keep it as acceptable.
        if l_cand is not None and l_cand.is_descendant_of(r_cand):
            cand, path = l_cand, l_path
        elif r_cand is not None and r_cand.is_descendant_of(l_cand):
            cand, path = r_cand, r_path
        elif l_cand is not None:
            cand, path = l_cand, l_path + r_path
        elif r_cand is not None:
            cand, path = r_cand, l_path + r_path
        else:
            return

        # The guidelines say:
        #    Within the relevant unit, a punctuation mark is attached
        #    at the highest possible node that preserves projectivity.
        # However, sometimes it is difficult to detect the unit (and its head).
        # E.g. in "Der Mann, den Sie gestern kennengelernt haben, kam wieder."
        # the second comma should depend on "kennengelernt", not on "Mann"
        # because the unit is just the relative clause.
        # We try to be conservative and keep the parent, unless we are sure it is wrong.
        if node.parent not in path:
            node.parent = cand
        node.deprel = "punct"

    def _will_be_projective(self, node, cand):
        node.parent = cand
        return not node.is_nonprojective() and not self._causes_gap(node)

    def _causes_gap(self, node):
        return node.is_nonprojective_gap() and not node.parent.is_nonprojective_gap()

    def _fix_paired_punct(self, root, opening_node, closing_punct):
        if (self.check_paired_punct_upos
            or opening_node.form == "'") and opening_node.upos != 'PUNCT':
            return

        nested_level = 0
        for node in root.descendants[opening_node.ord:]:
            if node.form == closing_punct:
                if nested_level > 0:
                    nested_level -= 1
                else:
                    self._fix_pair(root, opening_node, node)
                    return
            elif node.form == opening_node.form:
                nested_level += 1

    def _fix_pair(self, root, opening_node, closing_node):
        heads = []
        punct_heads = []
        for node in root.descendants[opening_node.ord: closing_node.ord - 1]:
            if node.parent.precedes(opening_node) or closing_node.precedes(node.parent):
                if node.upos == 'PUNCT':
                    punct_heads.append(node)
                else:
                    heads.append(node)

        # Punctuation should not have children, but if there is no other head candidate,
        # let's break this rule.
        if len(heads) == 0:
            heads = punct_heads
        # If there are no nodes between the opening and closing mark (),
        # let's treat the marks as any other (non-pair) punctuation.
        if len(heads) == 0:
            return
        else:
            # Ideally, there should be only a single head.
            # If not, we could try e.g. to choose the "widests-span head":
            #  opening_node.parent = sorted(heads, key=lambda n: n.descendants(add_self=1)[0].ord)[0]
            #  closing_node.parent = sorted(heads, key=lambda n: -n.descendants(add_self=1)[-1].ord)[0]
            # which often leads to selecting the same head for the opening and closing punctuation
            # ignoring single words inside the paired punct which are non-projectively attached outside.
            # However, this means that the paired punctuation will be attached non-projectively,
            # which is forbidden by the UD guidelines.
            # Thus, we will choose the nearest head, which is the only way how to prevent non-projectivities.
            opening_node.parent = heads[0]
            closing_node.parent = heads[-1]

        self._punct_type[opening_node.ord] = 'opening'
        self._punct_type[closing_node.ord] = 'closing'

        # In rare cases, non-projective gaps may remain. Let's dirty fix these!
        # E.g. in "the (lack of) reproducibility", the closing parenthesis
        # should be attached to "of" rather than to "lack"
        # -- breaking the paired-marks-have-same-parent rule
        # in order to prevent the punct-nonproj-gap bug (recently checked by validator.py).
        if self._causes_gap(opening_node):
            opening_node.parent = opening_node.next_node
            while (opening_node.parent.ord < closing_node.ord - 1
                and (opening_node.parent.upos == 'PUNCT' or opening_node.is_nonprojective()
                or self._causes_gap(opening_node))):
                    opening_node.parent = opening_node.parent.next_node
        if self._causes_gap(closing_node):
            closing_node.parent = closing_node.prev_node
            while (closing_node.parent.ord > opening_node.ord + 1
                and (closing_node.parent.upos == 'PUNCT' or closing_node.is_nonprojective()
                or self._causes_gap(closing_node))):
                    closing_node.parent = closing_node.parent.prev_node
