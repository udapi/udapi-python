"""Block ud.ro.SetSpaceAfter for heuristic setting of SpaceAfter=No in Romanian.

Usage::

  udapy -s ud.ro.SetSpaceAfter < in.conllu > fixed.conllu

Author: Martin Popel
"""
import re

import udapi.block.ud.setspaceafter


class SetSpaceAfter(udapi.block.ud.setspaceafter.SetSpaceAfter):
    """Block for heuristic setting of the SpaceAfter=No MISC attribute in Romanian.

    Romanian uses many contractions, e.g.

    =======  =======  =========  ==========
    raw      meaning  tokenized  lemmatized
    =======  =======  =========  ==========
    n-ar     nu ar    n- ar      nu avea
    să-i     să îi    să -i      să el
    într-o   în o     într- o    întru un
    nu-i     nu îi    nu -i      nu el
    nu-i     nu e     nu -i      nu fi
    =======  =======  =========  ==========

    Detokenization is quite simple: no space after word-final hyphen and before word-initial hyphen.
    There are just two exceptions, I have found:
    * "-" the hyphen itself (most probably it means a dash separating phrases/clauses)
    * negative numbers, e.g. "-3,1"
    """

    def process_tree(self, root):
        nodes = root.descendants
        for i, node in enumerate(nodes[:-1]):

            # Mark contractions like -i, -și, -l, -urilor, but not negative numbers like -12,3.
            # Store SpaceAfter=No to the previous node.
            next_form = nodes[i + 1].form
            if re.match('-.*[^0-9,.]', next_form):
                self.mark_no_space(node)

            # Mark contractions like s-, într-, și-, printr-.
            if node.form[-1] == '-' and node.form != '-':
                self.mark_no_space(node)

        super().process_tree(root)
