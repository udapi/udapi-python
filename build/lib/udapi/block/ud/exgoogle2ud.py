"""Block ud.ExGoogle2ud converts data which were originally annotated in Google style
then converted with an older version of ud.Google2ud to UDv2,
then manually edited and we don't want to loose these edits,
so we cannot simply rerun the newer version of ud.Google2ud on the original Google data.
"""
from udapi.block.ud.fixchain import FixChain
from udapi.block.ud.fixpunct import FixPunct
from udapi.block.ud.fixrightheaded import FixRightheaded
from udapi.block.ud.complywithtext import ComplyWithText
from udapi.block.ud.es.addmwt import AddMwt as es_AddMwt
from udapi.block.ud.joinasmwt import JoinAsMwt
from udapi.core.block import Block


class ExGoogle2ud(Block):
    """Convert former Google Universal Dependency Treebank into UD style."""

    def __init__(self, lang='unk', **kwargs):
        super().__init__(**kwargs)
        self.lang = lang

        self._fixpunct_block = None if self.lang == 'it' else FixPunct()
        self._fixrigheaded_block = FixRightheaded()
        self._fixchain_block = FixChain()
        self._comply_block = None
        if lang == 'ja':
            self._comply_block = ComplyWithText()

        self._addmwt_block = None
        self._joinasmwt_block = None
        if lang == 'es':
            self._addmwt_block = es_AddMwt()
            self._joinasmwt_block = JoinAsMwt()

    def process_tree(self, root):
        for node in root.descendants:
            self.fix_node(node)

        for block in (
                self._addmwt_block,
                self._joinasmwt_block,
                self._comply_block,
                self._fixrigheaded_block,  # deprel=fixed,flat,... should be always head-initial
                self._fixchain_block,      # and form a flat structure, not a chain.
                self._fixpunct_block):     # commas should depend on the subord unit.
            if block:
                block.process_tree(root)

    def fix_node(self, node):
        """Various fixed taken from ud.Google2ud."""

        if node.xpos == 'SYM':  # These are almost always tagged as upos=X which is wrong.
            node.upos = 'SYM'
            if node.deprel in {'punct', 'p'}:
                if node.form in "_-.؟”'":
                    node.upos = 'PUNCT'
                else:
                    node.deprel = 'dep'  # This is another way how to say deprel=todo.

        if self.lang != 'es' and node.udeprel == 'nmod' and node.deprel != 'nmod':
            parent_is_nominal = self.is_nominal(node.parent)
            if parent_is_nominal == 'no':
                node.deprel = 'obl' + ':' + node.sdeprel
            elif node.deprel == 'nmod:tmod':
                node.deprel = 'obl:tmod'

        if node.deprel == 'obl:gmod' and self.lang == 'ar':
            node.deprel = 'obl'
            node.feats['Case'] = 'Gen'

        if node.upos == 'CCONJ' and node.deprel == 'mark':
            node.upos = 'SCONJ'

        if self.lang == 'es':
            if node.deprel == 'compound':
                # most of the uppercase compounds are upos=PROPN, but not all, e.g. Hack Forums
                if node.form[0].isupper():
                    node.deprel = 'flat:name'
                else:
                    node.deprel = 'nmod'

    @staticmethod
    def is_nominal(node):
        """Returns 'no' (for predicates), 'yes' (sure nominals) or 'maybe'.

        Used in `change_nmod`."""
        if node.upos in ["VERB", "AUX", "ADJ", "ADV"]:
            return 'no'
        # Include NUM for examples such as "one of the guys"
        # and DET for examples such as "some/all of them"
        if node.upos in ["NOUN", "PRON", "PROPN", "NUM", "DET"]:
            # check whether the node is a predicate
            # (either has a nsubj/csubj dependendent or a copula dependent)
            if any(["subj" in child.deprel or child.deprel == 'cop' for child in node.children]):
                return 'maybe'
            return 'yes'
        return 'maybe'
