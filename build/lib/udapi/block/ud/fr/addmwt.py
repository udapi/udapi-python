"""Block ud.fr.AddMwt for heuristic detection of French contractions.

According to the UD guidelines, contractions such as "des" = "de les"
should be annotated using multi-word tokens.

Note that this block should be used only for converting legacy conllu files.
Ideally a tokenizer should have already split the MWTs.
"""
import udapi.block.ud.addmwt

MWTS = {
    'au':         {'form': 'à le', 'lemma': 'à le'},
    'aux':        {'form': 'à les', 'lemma': 'à le'},
    'des':        {'form': 'de les', 'lemma': 'de le'},
    'du':         {'form': 'de le', 'lemma': 'de le'},

    'auquel':     {'form': 'à lequel', 'upos': 'ADP PRON', 'lemma': 'à lequel'},
    'auxquels':   {'form': 'à lesquels', 'upos': 'ADP PRON', 'lemma': 'à lequel'},
    'auxquelles': {'form': 'à lesquelles', 'upos': 'ADP PRON', 'lemma': 'à lequel'},
    'desquels':   {'form': 'de lesquels', 'upos': 'ADP PRON', 'lemma': 'de lequel'},
    'desquelles': {'form': 'de lesquelles', 'upos': 'ADP PRON', 'lemma': 'de lequel'},
    'duquel':     {'form': 'de lequel', 'upos': 'ADP PRON', 'lemma': 'de lequel'},
}
# TODO https://fr.wiktionary.org/wiki/des#Vocabulaire_apparent.C3.A9_par_le_sens_2
# lists more contractions, e.g. "dudit", "audit"

# shared values for all entries in MWTS
for v in MWTS.values():
    if not v.get('upos'):
        v['upos'] = 'ADP DET'
    if not v.get('shape'):
        v['shape'] = 'subtree'
    if not v.get('deprel'):
        v['deprel'] = 'case det' if v['upos'] == 'ADP DET' else 'case *'
    if not v.get('main'):
        v['main'] = 1 if v['upos'] == 'ADP PRON' else 0
    v['feats'] = '_ *'


class AddMwt(udapi.block.ud.addmwt.AddMwt):
    """Detect and mark MWTs (split them into words and add the words to the tree)."""

    def multiword_analysis(self, node):
        """Return a dict with MWT info or None if `node` does not represent a multiword token."""

        # "du" can be
        # - "du + le" (tagged ADP)
        # - the partitive article "du" (tagged DET)
        # - past participle of devoir (correctly dû, tagged VERB)
        # Only the ADP case should be split.
        # Similarly with "des" -> "de les".
        if node.upos != 'ADP':
            return None

        return MWTS.get(node.form.lower(), None)

    # "du" has a shape which is neither "siblings" nor "subtree"
    # E.g. in "À partir du XXIe siècle"
    # "du" = "de le", but
    # "de" is attached to "À", while "le" is attached to "siècle".
    def postprocess_mwt(self, mwt):
        if mwt.form.lower() in {'du', 'des', 'au', 'aux'}:
            if mwt.words[0].descendants[-1] != mwt.words[1]:
                pass
            elif mwt.words[0].precedes(mwt.words[0].parent):
                mwt.words[1].parent = mwt.words[0].parent
            else:
                head = mwt.words[1].next_node
                while head.upos not in {'NOUN', 'PROPN'} and not head.is_root():
                    if head.parent.precedes(head):
                        head = mwt.words[1].next_node
                        break
                    head = head.parent
                if head.is_root():
                    head = mwt.words[1].next_node
                mwt.words[1].parent = head

        if mwt.words[1].parent == mwt.words[0] and mwt.words[0].descendants[-1].deprel == 'fixed':
            mwt.words[1].deprel = 'fixed'
        if (mwt.words[0].parent.precedes(mwt.words[0])
                and mwt.words[0].prev_node.udeprel in {'case', 'fixed'}):
            mwt.words[0].deprel = 'fixed'
