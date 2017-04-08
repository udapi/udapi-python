"""Block ud.el.AddMwt for heuristic detection of multi-word (σε+DET) tokens.

Notice that this should be used only for converting existing conllu files.
Ideally a tokenizer should have already split the MWTs.
Also notice that this block does not deal with the relatively rare
``PRON(Person=2)+'*+PRON(Person=3, i.e. "σ'το" and "στο")`` MWTs.
"""
import udapi.block.ud.addmwt

MWTS = {
    'στη':   {'form': 'σ τη', 'feats':   '_ Case=Acc|Gender=Fem|Number=Sing'},
    'στην':  {'form': 'σ την', 'feats':  '_ Case=Acc|Gender=Fem|Number=Sing'},
    'στα':   {'form': 'σ τα', 'feats':   '_ Case=Acc|Gender=Neut|Number=Plur'},
    'στους': {'form': 'σ τους', 'feats': '_ Case=Acc|Gender=Masc|Number=Plur'},
    'στις':  {'form': 'σ τις', 'feats':  '_ Case=Acc|Gender=Fem|Number=Plur'},
    'στον':  {'form': 'σ τον', 'feats':  '_ Case=Acc|Gender=Masc|Number=Sing'},
    'στο':   {'form': 'σ το', 'feats':   '_ Case=Acc|Gender=*|Number=Sing'},
}

# shared values for all entries in MWTS
for v in MWTS.values():
    v['lemma'] = 'σε ο'
    v['upos'] = 'ADP DET'
    v['xpos'] = 'AsPpSp AtDf'
    v['deprel'] = 'case det'
    # The following are the default values
    # v['main'] = 0 # which of the two words will inherit the original children (if any)
    # v['shape'] = 'siblings', # the newly created nodes will be siblings


class AddMwt(udapi.block.ud.addmwt.AddMwt):
    """Detect and mark MWTs (split them into words and add the words to the tree)."""

    def multiword_analysis(self, node):
        """Return a dict with MWT info or None if `node` does not represent a multiword token."""
        return MWTS.get(node.form.lower(), None)
