"""Block ud.RemoveMwt for removing multi-word tokens."""
from udapi.core.block import Block


class RemoveMwt(Block):
    """Substitute MWTs with one word representing the whole MWT."""

    def process_tree(self, root):
        for mwt in root.multiword_tokens:
            words = mwt.words
            words[0].form = mwt.form
            words[0].misc = mwt.misc
            words[0].upos = self.guess_upos(words)
            words[0].feats = self.guess_feats(words)
            words[0].deprel = self.guess_deprel(words)
            mwt.remove()
            for word in words[1:]:
                word.remove(children='rehang')

    @staticmethod
    def guess_upos(words):
        """UPOS of the whole MWT"""
        return words[0].upos

    @staticmethod
    def guess_deprel(words):
        """DEPREL of the whole MWT"""
        return words[0].deprel
        # Alternatively, we could define deprel subtypes
        # return words[0].deprel + ':' + ','.join([w.deprel for w in words[1:]])

    @staticmethod
    def guess_feats(words):
        """FEATS of the whole MWT"""
        feats = words[0].feats
        for word in words[1:]:
            feats.update(word.feats)
        return feats
