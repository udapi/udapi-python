"""Block ud.cs.AddMwt for heuristic detection of multi-word tokens."""
import udapi.block.ud.addmwt

MWTS = {
    'abych': {'form': 'aby bych', 'feats': '_ Mood=Cnd|Number=Sing|Person=1|VerbForm=Fin'},
    'kdybych': {'form': 'když bych', 'feats': '_ Mood=Cnd|Number=Sing|Person=1|VerbForm=Fin'},
    'abys': {'form': 'aby bys', 'feats': '_ Mood=Cnd|Number=Sing|Person=2|VerbForm=Fin'},
    'kdybys': {'form': 'když bys', 'feats': '_ Mood=Cnd|Number=Sing|Person=2|VerbForm=Fin'},
    'aby': {'form': 'aby by', 'feats': '_ Mood=Cnd|Person=3|VerbForm=Fin'},
    'kdyby': {'form': 'když by', 'feats': '_ Mood=Cnd|Person=3|VerbForm=Fin'},
    'abychom': {'form': 'aby bychom', 'feats': '_ Mood=Cnd|Number=Plur|Person=1|VerbForm=Fin'},
    'kdybychom': {'form': 'když bychom', 'feats': '_ Mood=Cnd|Number=Plur|Person=1|VerbForm=Fin'},
    'abyste': {'form': 'aby byste', 'feats': '_ Mood=Cnd|Number=Plur|Person=2|VerbForm=Fin'},
    'kdybyste': {'form': 'když byste', 'feats': '_ Mood=Cnd|Number=Plur|Person=2|VerbForm=Fin'},
}
for v in MWTS.values():
    v['upos'] = 'SCONJ AUX'
    number = '-'
    if 'Sing' in v['feats']:
        number = 'S'
    elif 'Plur' in v['feats']:
        number = 'P'
    person = '-'
    if 'Person=1' in v['feats']:
        person = '1'
    elif 'Person=2' in v['feats']:
        person = '2'

    v['xpos'] = 'J,------------- Vc-%s---%s-------' % (number, person)
    v['deprel'] = '* aux'
    v['lemma'] = v['form'].split()[0] + ' být'
    v['main'] = 0
    v['shape'] = 'siblings'

# nač -> na + co
for prep in 'na za o'.split():
    MWTS[prep + 'č'] = {
        'form': prep + ' co',
        'lemma': prep + ' co',
        'upos': 'ADP PRON',
        'deprel': 'case *',
        'main': 1,
        'shape': 'subtree',
    }


class AddMwt(udapi.block.ud.addmwt.AddMwt):
    """Detect and mark MWTs (split them into words and add the words to the tree)."""

    def multiword_analysis(self, node):
        """Return a dict with MWT info or None if `node` does not represent a multiword token."""
        analysis = MWTS.get(node.form.lower(), None)
        if analysis is not None:
            return analysis

        # There is no VerbType=verbconj in the UD_Czech data.
        # The purpose of this rule is rather to show that
        # it is possible to write such "dynamic" rules
        # (which cannot be included in static MWTS).
        if node.form.lower().endswith('ť') and node.feats['VerbType'] == 'verbconj':
            return {
                'form': node.form.lower()[:-1] + ' neboť',
                'lemma': '* neboť',
                'upos': '* CCONJ',
                'xpos': 'Vt-S---3P-NA--2 J^-------------',
                'feats': '* _',
                'deprel': '* cc',
                'main': 0,
                'shape': 'subtree',
            }
        return None

    def postprocess_mwt(self, mwt):
        if mwt.words[0].deprel == 'fixed' and mwt.words[0].parent.parent.upos == 'VERB':
            mwt.words[1].parent = mwt.words[0].parent.parent
