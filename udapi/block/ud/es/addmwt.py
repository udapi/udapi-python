"""Block ud.es.AddMwt for heuristic detection of Spanish contractions.

According to the UD guidelines, contractions such as "del" = "de el"
should be annotated using multi-word tokens.

Note that this block should be used only for converting legacy conllu files.
Ideally a tokenizer should have already split the MWTs.
"""
import re
import udapi.block.ud.addmwt

MWTS = {
    'al':      {'form': 'a el'},
    'del':     {'form': 'de el'},
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
    v['deprel'] = '* det'
    v['feats'] = '_ Definite=Def|Gender=Masc|Number=Sing|PronType=Art'
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

        if not self.verbpron or node.upos not in {'VERB', 'AUX'}:
            return None

        form = node.form.lower()

        if re.search('(me|la|le|lo|se|te)$', form):
            verbform = node.feats['VerbForm']
            # TODO there are contractions even with VerbForm=Fin
            if verbform == 'Fin' or form == 'pese':
                return None
            del node.feats['VerbForm']
            pron = form[-2:]
            return {
                'form': form[:-2] + ' ' + pron,
                'lemma': '* ' + LEMMA[pron],
                'upos': '* PRON',
                'feats': 'VerbForm=%s *' % verbform,
                'deprel': '* iobj',
                'main': 0,
                'shape': 'subtree',
            }

        if re.search('l[oe]s$', form):
            verbform = node.feats['VerbForm']
            if verbform == 'Fin':
                return None
            del node.feats['VerbForm']
            pron = form[-3:]
            return {
                'form': form[:-3] + ' ' + pron,
                'lemma': '* él',
                'upos': '* PRON',
                'feats': 'VerbForm=%s *' % verbform,
                'deprel': '* iobj',
                'main': 0,
                'shape': 'subtree',
            }

        # TODO: multiple suffixes, e.g. compratelo = compra + te + lo
        return None

    # Sometimes "del" has a shape which is neither "siblings" nor "subtree".
    # E.g. in "a partir del NOUN"
    # "del" = "de el", but
    # "de" is attached to "a" (as fixed), while "el" is attached to the NOUN.
    def postprocess_mwt(self, mwt):
        if mwt.form.lower() in {'al', 'del'} and mwt.words[1].parent.precedes(mwt.words[1]):
            head = mwt.words[1].next_node
            while head.upos not in {'NOUN', 'PROPN'}:
                if head.parent.precedes(head) or head.is_root():
                    head = mwt.words[1].next_node
                    break
                head = head.parent
            mwt.words[1].parent = head
