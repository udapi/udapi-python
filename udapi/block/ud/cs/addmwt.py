"""Block ud.cs.AddMwt for heuristic detection of multi-word tokens."""
import udapi.block.ud.addmwt
import re
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

# Define static rules for 'nač', 'oč', 'zač' (but not 'proč').
# Add them to the already existing dictionary MWTS.
# nač -> na + co
for prep in 'na o za'.split():
    MWTS[prep + 'č'] = {
        'form': prep + ' co',
        'lemma': prep + ' co',
        'upos': 'ADP PRON',
        'xpos': 'RR--4---------- PQ--4----------',
        'feats': 'AdpType=Prep|Case=Acc Animacy=Inan|Case=Acc|PronType=Int,Rel',
        'deprel': 'case *',
        'main': 1,
        'shape': 'subtree',
    }

# Define static rules for 'naň', 'oň', 'proň', 'zaň'.
# Add them to the already existing dictionary MWTS.
# naň -> na + něj
for prep in 'na o pro za'.split():
    MWTS[prep + 'ň'] = {
        'form': prep + ' něj',
        'lemma': prep + ' on',
        'upos': 'ADP PRON',
        'xpos': 'RR--4---------- PEZS4--3-------',
        'feats': 'AdpType=Prep|Case=Acc Case=Acc|Gender=Masc,Neut|Number=Sing|Person=3|PrepCase=Pre|PronType=Prs',
        'deprel': 'case *',
        'main': 1,
        'shape': 'subtree',
    }
# Additional contractions in Old Czech with vocalization.
for prep in 'přěd'.split():
    preplemma = re.sub(r"ě", r"e", prep)
    MWTS[prep + 'eň'] = {
        'form': prep + ' něj',
        'lemma': preplemma + ' on',
        'upos': 'ADP PRON',
        'xpos': 'RV--4---------- PEZS4--3-------',
        'feats': 'AdpType=Voc|Case=Acc Case=Acc|Gender=Masc,Neut|Number=Sing|Person=3|PrepCase=Pre|PronType=Prs',
        'deprel': 'case *',
        'main': 1,
        'shape': 'subtree',
    }

# Define static rules for 'naňž', 'oňž', 'proňž', 'zaňž'.
# Add them to the already existing dictionary MWTS.
# naňž -> na + nějž
for prep in 'na o pro za'.split():
    MWTS[prep + 'ňž'] = {
        'form': prep + ' nějž',
        'lemma': prep + ' jenž',
        'upos': 'ADP PRON',
        'xpos': 'RR--4---------- P4ZS4---------2',
        'feats': 'AdpType=Prep|Case=Acc Case=Acc|Gender=Masc,Neut|Number=Sing|PrepCase=Pre|PronType=Rel',
        'deprel': 'case *',
        'main': 1,
        'shape': 'subtree',
    }

class AddMwt(udapi.block.ud.addmwt.AddMwt):
    """Detect and mark MWTs (split them into words and add the words to the tree)."""

    def multiword_analysis(self, node):
        """Return a dict with MWT info or None if `node` does not represent a multiword token."""
        # Avoid adding a MWT if the current node already is part of an MWT.
        if node.multiword_token:
            return None
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
