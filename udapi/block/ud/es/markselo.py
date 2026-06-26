"""
This block searches for Spanish ditransitive verbs with two clitics (e.g. 'dárselo').
The hypothesis is that in most such cases, 'se' just substitutes for 'le' or 'les'
and is not reflexive.
"""
from udapi.core.block import Block

class MarkSeLo(Block):

    def process_node(self, node):
        if node.upos == 'VERB':
            se_children = [x for x in node.children if x.form.lower() == 'se']
            if len(se_children) >= 1:
                lo_children = [x for x in node.children if x.form.lower() in ['lo', 'la', 'los', 'las']]
                if len(lo_children) >= 1:
                    # Annotation errors lead to patterns like "los que se esperan".
                    # Therefore, require that "se" and "lo" are adjacent.
                    if abs(se_children[0].ord-lo_children[0].ord) == 1:
                        # We expect 1 se and 1 lo, not more.
                        # Nevertheless, for the moment, mark them all.
                        for x in se_children:
                            x.misc['Mark'] = 'se'
                        for x in lo_children:
                            x.misc['Mark'] = 'lo'
                        node.misc['Mark'] = 'VERB'
