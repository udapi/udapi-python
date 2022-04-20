"""Block to fix spurious auxiliary verbs in UD Spanish-AnCora."""
from udapi.core.block import Block
import logging
import re

class FixTenerQue(Block):

    def process_node(self, node):
        """
        Some Spanish treebanks treat the verb 'tener' in constructions such as
        'tener que comer' as auxiliary. This is wrong and the validator will
        flag it as an error. This block fixes such annotations.
        """
        if node.lemma == 'tener' and node.upos == 'AUX':
            node.upos = 'VERB'
            # In rare cases the auxiliary may have been promoted due to ellipsis.
            # Most of the time however, it is attached as 'aux' to the main verb.
            if node.udeprel == 'aux':
                mainverb = node.parent
                node.parent = mainverb.parent
                node.deprel = mainverb.deprel
                mainverb.parent = node
                mainverb.deprel = 'xcomp'
                # Some children of the former main verb should be reattached to 'tener'.
                # Others (especially a direct object) should stay with the former main verb.
                for c in mainverb.children:
                    if not re.match(r'^(obj|iobj|obl|conj|list|flat|fixed|goeswith|reparandum)$', c.udeprel):
                        c.parent = node
                # On the other hand, the conjunction 'que' may have been wrongly attached as 'fixed' to 'tener'.
                for c in node.children:
                    if c.form.lower() eq 'que' and c.ord > node.ord and c.ord < mainverb.ord:
                        c.parent = mainverb
                        c.deprel = 'mark'
