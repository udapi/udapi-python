"""Block ud.gl.To2 UD_Galician-specific conversion of UDv1 to UDv2

Author: Martin Popel
"""
from udapi.core.block import Block

ADP_HEAD_PREFERENCES = {
    'NOUN': 10,
    'PRON': 9,
    'ADJ': 8,
    'VERB': 8,
    'PUNCT': -10,
}


class To2(Block):
    """Block for fixing the remaining cases (before ud.Convert1to2) in UD_Galician."""

    def process_node(self, node):

        # UD_Galician v1.4 uses incorrectly deprel=cop not for the copula verb,
        # but for its complement (typically ADJ) and also copula is the head.
        if node.deprel == 'cop':
            copula = node.parent
            # In UDv2 discussions it has been decided that only a limited set of verbs
            # can be annotated as copula. For Spanish, "estar" was questionable, but accepted.
            # I guess in Galician it is the same. The rest (considerar, resultar, quedar,...)
            # should not be annotated as copulas. Luckily, in UD_Galician v1.4 they are
            # governing the clause, so no change of topology is needed, just deprel=xcomp.
            if copula.lemma in ('ser', 'estar'):
                node.parent = copula.parent
                for cop_child in copula.children:
                    cop_child.parent = node
                copula.parent = node
                node.deprel = copula.deprel
                copula.deprel = 'cop'
            else:
                node.deprel = 'xcomp'

        # Prepositions should depend on the noun, not vice versa.
        # This is easy to fix, but unfortunatelly, there are many nodes with deprel=case
        # which are not actually prepostions or case markes, but standard NOUNs, VERBs etc.
        # These are left as ToDo.
        if node.deprel == 'case' and node.children:
            if node.upos not in ('ADP', 'CONJ', 'PART'):
                node.misc['ToDo'] = 'case-upos'
            else:
                children = sorted(node.children, key=lambda n: -ADP_HEAD_PREFERENCES.get(n.upos, 0))
                children[0].parent = node.parent
                node.parent = children[0]
                for child in children[1:]:
                    child.parent = children[0]

        # Punctuation should have no children.
        if node.deprel == 'punct' and node.children and node.upos == 'PUNCT':
            children = sorted(node.children, key=lambda n: -ADP_HEAD_PREFERENCES.get(n.upos, 0))
            children[0].parent = node.parent
            node.parent = children[0]
            for child in children[1:]:
                child.parent = children[0]
