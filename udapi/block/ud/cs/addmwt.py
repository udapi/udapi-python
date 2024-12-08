"""Block ud.cs.AddMwt for heuristic detection of multi-word tokens."""
import udapi.block.ud.addmwt
import re
import logging

# Define static rules for 'aby', 'kdyby' and similar forms.
MWTS = {
    'abych': {'form': 'aby bych', 'feats': '_ Aspect=Imp|Mood=Cnd|Number=Sing|Person=1|VerbForm=Fin'},
    'kdybych': {'form': 'když bych', 'feats': '_ Aspect=Imp|Mood=Cnd|Number=Sing|Person=1|VerbForm=Fin'},
    'abys': {'form': 'aby bys', 'feats': '_ Aspect=Imp|Mood=Cnd|Number=Sing|Person=2|VerbForm=Fin'},
    'kdybys': {'form': 'když bys', 'feats': '_ Aspect=Imp|Mood=Cnd|Number=Sing|Person=2|VerbForm=Fin'},
    'aby': {'form': 'aby by', 'feats': '_ Aspect=Imp|Mood=Cnd|VerbForm=Fin'},
    'kdyby': {'form': 'když by', 'feats': '_ Aspect=Imp|Mood=Cnd|VerbForm=Fin'},
    'abychom': {'form': 'aby bychom', 'feats': '_ Aspect=Imp|Mood=Cnd|Number=Plur|Person=1|VerbForm=Fin'},
    'kdybychom': {'form': 'když bychom', 'feats': '_ Aspect=Imp|Mood=Cnd|Number=Plur|Person=1|VerbForm=Fin'},
    # Old Czech 'abychme' == Modern Czech 'abychom'
    'abychme': {'form': 'aby bychme', 'feats': '_ Aspect=Imp|Mood=Cnd|Number=Plur|Person=1|VerbForm=Fin'},
    'kdybychme': {'form': 'když bychme', 'feats': '_ Aspect=Imp|Mood=Cnd|Number=Plur|Person=1|VerbForm=Fin'},
    'abyste': {'form': 'aby byste', 'feats': '_ Aspect=Imp|Mood=Cnd|Number=Plur|Person=2|VerbForm=Fin'},
    'kdybyste': {'form': 'když byste', 'feats': '_ Aspect=Imp|Mood=Cnd|Number=Plur|Person=2|VerbForm=Fin'},
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
            if subtokens[1] == 'jsi':
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
            if subtokens[1] == 'i':
                node.misc['AddMwt'] = ''
                return {
                    'form':   subtokens[0] + ' i',
                    'lemma':  '* i',
                    'upos':   '* CCONJ',
                    'xpos':   '* J^-------------',
                    'feats':  '* _',
                    'deprel': '* cc',
                    'main':   0,
                    'shape': 'subtree',
                }
            if subtokens[1] == 'ť':
                if token_from_subtokens != node.form:
                    logging.warning("Concatenation of MISC 'AddMwt=%s' does not yield the FORM '%s'." % (node.misc['AddMwt'], node.form))
                    return None
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
            # Contractions of prepositions and pronouns almost could be processed
            # regardless of AddMwt instructions by the annotator, but we still
            # require it to be on the safe side. For example, both 'přědeň' and
            # 'přěden' are attested in Old Czech but then we do not want to catch
            # 'on' (besides the wanted 'oň'). Another reason si that the pronoun
            # could be masculine or neuter. We pick Gender=Masc and Animacy=Anim
            # by default, unless the original token was annotated as Animacy=Inan
            # or Gender=Neut.
            m = re.match(r"^(na|o|pro|přěde|ski?rz[eě]|za)[nň](ž?)$", node.form.lower())
            if m:
                node.misc['AddMwt'] = ''
                # Remove vocalization from 'přěde' (přěd něj) but keep it in 'skrze'
                # (skrze něj).
                if m.group(1) == 'přěde':
                    pform = 'přěd'
                    plemma = 'před'
                    adptype = 'Voc'
                    at = 'V'
                elif re.match(r"^ski?rz[eě]$", m.group(1).lower()):
                    pform = m.group(1)
                    plemma = 'skrz'
                    adptype = 'Voc'
                    at = 'V'
                else:
                    pform = m.group(1)
                    plemma = m.group(1)
                    adptype = 'Prep'
                    at = 'R'
                # In UD PDT, Gender=Masc,Neut, and in PDT it is PEZS4--3 / P4ZS4---.
                if node.feats['Gender'] == 'Neut':
                    gender = 'Neut'
                    animacy = ''
                    g = 'N'
                elif node.feats['Animacy'] == 'Inan':
                    gender = 'Masc'
                    animacy = 'Animacy=Inan|'
                    g = 'I'
                else:
                    gender = 'Masc'
                    animacy = 'Animacy=Anim|'
                    g = 'M'
                if m.group(2).lower() == 'ž':
                    return {
                        'form': pform + ' nějž',
                        'lemma': plemma + ' jenž',
                        'upos': 'ADP PRON',
                        'xpos': 'R'+at+'--4---------- P4'+g+'S4---------2',
                        'feats': 'AdpType='+adptype+'|Case=Acc '+animacy+'Case=Acc|Gender='+gender+'|Number=Sing|PrepCase=Pre|PronType=Rel',
                        'deprel': 'case *',
                        'main': 1,
                        'shape': 'subtree',
                    }
                else:
                    return {
                        'form': pform + ' něj',
                        'lemma': plemma + ' on',
                        'upos': 'ADP PRON',
                        'xpos': 'R'+at+'--4---------- PE'+g+'S4--3-------',
                        'feats': 'AdpType='+adptype+'|Case=Acc '+animacy+'Case=Acc|Gender='+gender+'|Number=Sing|Person=3|PrepCase=Pre|PronType=Prs',
                        'deprel': 'case *',
                        'main': 1,
                        'shape': 'subtree',
                    }
        return None

    def postprocess_mwt(self, mwt):
        if mwt.words[0].deprel == 'fixed' and mwt.words[0].parent.parent.upos == 'VERB':
            mwt.words[1].parent = mwt.words[0].parent.parent
