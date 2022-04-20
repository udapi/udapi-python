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

        EDIT: 'ir a comer' is processed the same way.
        """
        if re.match(r'^(tener|ir)$', node.lemma) and node.upos == 'AUX':
            node.upos = 'VERB'
            # In rare cases the auxiliary may have been promoted due to ellipsis.
            # Most of the time however, it is attached as 'aux' to the main verb.
            if node.udeprel == 'aux':
                mainverb = node.parent
                self.reattach(node, mainverb.parent, mainverb.deprel)
                self.reattach(mainverb, node, 'xcomp')
                # Some children of the former main verb should be reattached to 'tener'.
                # Others (especially a direct object) should stay with the former main verb.
                for c in mainverb.children:
                    if not re.match(r'^(obj|iobj|obl|ccomp|xcomp|conj|list|compound|flat|fixed|goeswith|reparandum)$', c.udeprel):
                        self.reattach(c, node, c.deprel)
                # On the other hand, the conjunction 'que' may have been wrongly attached as 'fixed' to 'tener'.
                for c in node.children:
                    if re.match(r'^(que|a)$', c.form.lower()) and c.ord > node.ord and c.ord < mainverb.ord:
                        self.reattach(c, mainverb, 'mark')

    def reattach(self, node, parent, deprel):
        """
        Changes the incoming dependency relation to a node. Makes sure that the
        same change is done in the basic tree and in the enhanced graph.
        """
        if node.deps:
            # If the enhanced graph contains the current basic relation, remove it.
            orig_n_deps = len(node.deps)
            node.deps = [x for x in node.deps if x['parent'] != node.parent or re.sub(r':.*', '', x['deprel']) != node.udeprel]
            # Add the new basic relation to the enhanced graph only if the original one was there.
            if len(node.deps) < orig_n_deps:
                node.deps.append({'parent': parent, 'deprel': deprel})
        node.parent = parent
        node.deprel = deprel
