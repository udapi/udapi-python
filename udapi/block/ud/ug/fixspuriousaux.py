"""Block to convert spurious auxiliaries to lexical verbs in Uyghur."""
from udapi.core.block import Block
import logging
import re

class FixSpuriousAux(Block):

    def process_node(self, node):
        """
        Some verbs that are called auxiliary by the traditional grammar, should
        be analyzed in UD as VERB + non-finite xcomp.
        """
        # Sometimes there is a double error: it should not be auxiliary, it is
        # attached as aux but it is not tagged AUX. So we only look at the deprel.
        if node.udeprel == 'aux':
            # بەر/بار = give (used with actions done for the benefit of somebody)
            # چىق = go out
            # چىقىش = come out
            # يۈر = walk (the equivalent in Kazakh is considered to be a progressive auxiliary but it does not seem to be the case in Uyghur)
            # ئولتۇر = sit (the equivalent in Kazakh is considered to be a progressive auxiliary but it does not seem to be the case in Uyghur)
            # باق = do ever?
            # ئۆت = pass
            # كۆرۈش = see
            # باشلى = start
            # يەت = be enough
            # قايت = return
            # چۈش = fall down
            # قىل = do
            # چاپ = jump
            # قورق = fear
            # كەلتۈر = cause
            # كىر = enter
            # _ ... some putative auxiliaries do not even have a lemma
            if re.match(r'^(بەر|بار|چىق|چىقىش|يۈر|ئولتۇر|باق|ئۆت|_|كۆرۈش|باشلى|يەت|قايت|چۈش|قىل|چاپ|قورق|كەلتۈر|كىر)$', node.lemma):
                node.upos = 'VERB'
                # The auxiliary inherits the incoming relation of its original parent.
                lexverb = node.parent
                node.parent = lexverb.parent
                node.deprel = lexverb.deprel
                # The auxiliary also inherits some but not all children of the lexical verb.
                for c in lexverb.children:
                    if re.match(r'^(nsubj|csubj|obl|advmod|advcl|vocative|discourse|parataxis|punct)$', c.udeprel):
                        c.parent = node
                # The lexical verb becomes an xcomp of the auxiliary.
                lexverb.parent = node
                lexverb.deprel = 'xcomp'
