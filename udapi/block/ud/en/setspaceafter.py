"""Block ud.en.SetSpaceAfter for heuristic setting of SpaceAfter=No in English.

Usage::

  udapy -s ud.en.SetSpaceAfter < in.conllu > fixed.conllu

Author: Martin Popel
"""
import udapi.block.ud.setspaceafter


class SetSpaceAfter(udapi.block.ud.setspaceafter.SetSpaceAfter):
    """Block for heuristic setting of the SpaceAfter=No MISC attribute in English.

    """

    def process_tree(self, root):
        nodes = root.descendants
        for i, node in enumerate(nodes[:-1]):
            next_form = nodes[i + 1].form
            
            # Contractions like "don't" and possessive suffix 's should be annotated as MWT.
            # However, older UD_English-EWT versions did not follow this rule and even v2.7
            # contains some forgotten occurrences, so let's handle these as well.           
            if next_form in {"n't", "'s"}:
                self.mark_no_space(node)

            # Parsers may distinguish opening and closing single quotes by XPOS.
            elif node.form == "'" and node.xpos == "``":
                self.mark_no_space(node)
            elif next_form == "'" and nodes[i + 1].xpos == "''":
                self.mark_no_space(node)


            # hyphen-compounds
            elif node.form == '-' and i:
                if ((nodes[i - 1] is node.parent or nodes[i - 1].parent is node.parent) and
                    (nodes[i + 1] is node.parent or nodes[i + 1].parent is node.parent)):
                    self.mark_no_space(nodes[i - 1])
                    self.mark_no_space(node)
            
            # $200
            elif node.form == '$' and nodes[i + 1].upos == 'NUM':
                self.mark_no_space(node)

        super().process_tree(root)
