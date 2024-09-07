"""Block ud.cs.AddMwt for heuristic detection of multi-word tokens."""
import udapi.block.ud.addmwt
import logging

# Define static rules for 'aby', 'kdyby' and similar forms.
MWTS = {
    'abych': {'form': 'aby bych', 'feats': '_ Mood=Cnd|Number=Sing|Person=1|VerbForm=Fin'},
    'kdybych': {'form': 'když bych', 'feats': '_ Mood=Cnd|Number=Sing|Person=1|VerbForm=Fin'},
    'abys': {'form': 'aby bys', 'feats': '_ Mood=Cnd|Number=Sing|Person=2|VerbForm=Fin'},
    'kdybys': {'form': 'když bys', 'feats': '_ Mood=Cnd|Number=Sing|Person=2|VerbForm=Fin'},
    'aby': {'form': 'aby by', 'feats': '_ Mood=Cnd|VerbForm=Fin'},
    'kdyby': {'form': 'když by', 'feats': '_ Mood=Cnd|VerbForm=Fin'},
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

# Define static rules for 'nač', 'zač', 'oč' (but not 'proč').
# Add them to the already existing dictionary MWTS.
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
        # If the node did not match any of the static rules defined in MWTS,
        # check it against the "dynamic" rules below. The enclitic 'ť' will be
        # separated from its host but only if it has been marked by an annotator
        # in MISC. (These are annotation conventions used for Old Czech in the
        # Hičkok project.)
        if node.misc['AddMwt'] != '':
            subtokens = node.misc['AddMwt'].split()
            if len(subtokens) != 2:
                logging.warning("MISC 'AddMwt=%s' has unexpected number of subtokens." % node.misc['AddMwt'])
                return None
            token_from_subtokens = ''.join(subtokens)
            if token_from_subtokens != node.form:
                logging.warning("Concatenation of MISC 'AddMwt=%s' does not yield the FORM '%s'." % (node.misc['AddMwt'], node.form))
                return None
            if subtokens[1] == 's':
                node.misc['AddMwt'] = ''
                return {
                    'form':   subtokens[0] + ' jsi',
                    'lemma':  '* být',
                    'upos':   '* AUX',
                    'xpos':   '* VB-S---2P-AAI--',
                    'feats':  '* Aspect=Imp|Mood=Ind|Number=Sing|Person=2|Polarity=Pos|Tense=Pres|VerbForm=Fin|Voice=Act',
                    'deprel': '* aux',
                    'main':   0,
                    'shape':  'subtree' if node.upos in ['VERB'] else 'siblings',
                }
            if subtokens[1] == 'ť':
                node.misc['AddMwt'] = ''
                return {
                    'form':   node.form.lower()[:-1] + ' ť',
                    'lemma':  '* ť',
                    'upos':   '* PART',
                    'xpos':   '* TT-------------',
                    'feats':  '* _',
                    'deprel': '* discourse',
                    'main':   0,
                    'shape':  'subtree',
                }
        return None

    def postprocess_mwt(self, mwt):
        if mwt.words[0].deprel == 'fixed' and mwt.words[0].parent.parent.upos == 'VERB':
            mwt.words[1].parent = mwt.words[0].parent.parent
