"""Block ud.de.AddMwt for heuristic detection of German contractions.

According to the UD guidelines, contractions such as "am" = "an dem"
should be annotated using multi-word tokens.

Notice that this should be used only for converting existing conllu files.
Ideally a tokenizer should have already split the MWTs.
"""
import udapi.block.ud.addmwt

MWTS = {
    'am':      {'form': 'an dem', },
    'ans':     {'form': 'an das', },
    'aufs':    {'form': 'auf das', },
    'beim':    {'form': 'bei dem', },
    'durchs':  {'form': 'durch das', },
    'fürs':    {'form': 'fürs das', },
    'hinterm': {'form': 'hinter dem', },
    'hinters': {'form': 'hinter das', },
    'im':      {'form': 'in dem', },
    'ins':     {'form': 'in das', },
    'übers':   {'form': 'über das', },
    'ums':     {'form': 'um das', },
    'unterm':  {'form': 'unter dem', },
    'unters':  {'form': 'unter das', },
    'vom':     {'form': 'von dem', },
    'vorm':    {'form': 'vor dem', },
    'vors':    {'form': 'vor das', },
    'zum':     {'form': 'zu dem', },
    'zur':     {'form': 'zu der', },
}

# shared values for all entries in MWTS
for v in MWTS.values():
    v['lemma'] = v['form'].split()[0] + ' der'
    v['upos'] = 'ADP DET'
    v['xpos'] = 'APPR ART'
    v['deprel'] = 'case det'
    v['feats'] = '_ *'
    # The following are the default values
    # v['main'] = 0 # which of the two words will inherit the original children (if any)
    # v['shape'] = 'siblings', # the newly created nodes will be siblings


class AddMwt(udapi.block.ud.addmwt.AddMwt):
    """Detect and mark MWTs (split them into words and add the words to the tree)."""

    def multiword_analysis(self, node):
        """Return a dict with MWT info or None if `node` does not represent a multiword token."""
        return MWTS.get(node.form.lower(), None)
