"""Block ud.gl.AddMwt for heuristic detection of Galician contractions.

According to the UD guidelines, contractions such as "do" = "de o"
should be annotated using multi-word tokens.

Note that this block should be used only for converting legacy conllu files.
Ideally a tokenizer should have already split the MWTs.
"""
import re
import udapi.block.ud.addmwt

MWTS = {
    'ao':      {'form': 'a o'},
    'á':       {'form': 'a a'},
    'aos':     {'form': 'a os'},
    'ás':      {'form': 'a as'},
    'do':      {'form': 'de o'},
}

LEMMA = {
    'se': 'él',
    'le': 'él',
    'la': 'él',
    'lo': 'él',
    'te': 'tú',
    'me': 'yo',
}

# shared values for all entries in MWTS
for v in MWTS.values():
    v['lemma'] = v['form']
    v['upos'] = 'ADP DET'
    v['deprel'] = 'case det'
    forms = v['form'].split(' ')
    if forms[1] == 'o':
        v['feats'] = '_ Definite=Def|Gender=Masc|Number=Sing|PronType=Art'
        v['xpos'] = 'SPS00 DA0MS0'
    elif forms[1] == 'os':
        v['feats'] = '_ Definite=Def|Gender=Masc|Number=Plur|PronType=Art'
        v['xpos'] = 'SPS00 DA0MP0'
    elif forms[1] == 'a':
        v['feats'] = '_ Definite=Def|Gender=Fem|Number=Sing|PronType=Art'
        v['xpos'] = 'SPS00 DA0FS0'
    elif forms[1] == 'as':
        v['feats'] = '_ Definite=Def|Gender=Fem|Number=Plur|PronType=Art'
        v['xpos'] = 'SPS00 DA0FP0'
    # The following are the default values
    # v['main'] = 0 # which of the two words will inherit the original children (if any)
    # v['shape'] = 'siblings', # the newly created nodes will be siblings


class AddMwt(udapi.block.ud.addmwt.AddMwt):
    """Detect and mark MWTs (split them into words and add the words to the tree)."""

    def __init__(self, verbpron=False, **kwargs):
        super().__init__(**kwargs)
        self.verbpron = verbpron

    def multiword_analysis(self, node):
        """Return a dict with MWT info or None if `node` does not represent a multiword token."""
        analysis = MWTS.get(node.form.lower(), None)

        if analysis is not None:
            # Modify the default attachment of the new syntactic words in special situations.
            if re.match(r'^(root|conj|reparandum)$', node.udeprel):
                # Copy the dictionary so that we do not modify the original and do not affect subsequent usages.
                analysis = analysis.copy()
                analysis['shape'] = 'subtree'
            return analysis
        return None

    # Sometimes "do" has a shape which is neither "siblings" nor "subtree".
    # E.g. in "a partir do NOUN"
    # "do" = "de o", but
    # "de" is attached to "a" (as fixed), while "o" is attached to the NOUN.
    def postprocess_mwt(self, mwt):
        #if mwt.form.lower() in {'ao', 'do'} and mwt.words[1].parent.precedes(mwt.words[1]):
        if mwt.words[1].parent.precedes(mwt.words[1]):
            head = mwt.words[1].next_node
            while head.upos not in {'NOUN', 'PROPN'}:
                if head.parent.precedes(head) or head.is_root():
                    head = mwt.words[1].next_node
                    break
                head = head.parent
            mwt.words[1].parent = head
