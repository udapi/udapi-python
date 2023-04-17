"""Block ud.pt.AddHyphenMwt for transforming hyphen compounds into multiword tokens in Portuguese-GSD.

See https://github.com/UniversalDependencies/UD_Portuguese-GSD/issues/39
"""
from udapi.core.block import Block

class AddHyphenMwt(Block):

    def _ok(self, token):
        # The hyphen in "al-Assad" perhaps should be kept as a separate word.
        return token.form.isalnum() and token.form.lower() != 'al'

    def process_tree(self, root):
        tokens, i = root.token_descendants, 1
        while i+1 < len(tokens):
            start_i = i-1
            if tokens[i].form == "-" and self._ok(tokens[i-1]) and self._ok(tokens[i+1]):
                while i+3 < len(tokens) and tokens[i+2].form == "-" and self._ok(tokens[i+3]):
                    i += 2
                compound, words = tokens[start_i:i+2], []
                for token in compound:
                    words += token.words
                heads = [w for w in words if w.parent not in words]
                cuckolds = [w for w in words if w not in heads and any(c not in words for c in w.children)]
                if len(heads) > 1:
                    for h in heads:
                        h.misc["ToDo"] = 'NonCatenaCompound'
                elif cuckolds:
                    for c in cuckolds:
                        c.misc["ToDo"] = 'HasChildrenOutsideCompound'
                else:
                    compound_form = "".join(t.form for t in compound)
                    for hyphen in compound[1::2]:
                        hyphen.remove()
                    root.create_multiword_token([w for w in words if w.form != '-'], compound_form)
                    root.text = None
            i += 1
