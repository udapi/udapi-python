"""Block ud.pt.AddMwt for heuristic detection of Portuguese contractions.

According to the UD guidelines, contractions such as "dele" = "de ele"
should be annotated using multi-word tokens.

Note that this block should be used only for converting legacy conllu files.
Ideally a tokenizer should have already split the MWTs.
"""
import udapi.block.ud.addmwt

MWTS = {
    'à':       {'form': 'a a', 'lemma': 'a o'},
    'às':      {'form': 'a as', 'lemma': 'a o'},
    # 'ao':      {'form': 'a o', 'lemma': 'a o'},  # Sometimes annotated just as ao/ao/ADP/case
    'aos':     {'form': 'a os', 'lemma': 'a o'},
    'da':      {'form': 'de a', 'lemma': 'de o'},
    'das':     {'form': 'de as', 'lemma': 'de o'},
    'desta':   {'form': 'de esta', 'lemma': 'de este'},
    'dele':    {'form': 'de ele', 'lemma': 'de ele', 'upos': 'ADP PRON', 'deprel': 'case *'},
    'deles':   {'form': 'de eles', 'lemma': 'de eles', 'upos': 'ADP PRON', 'deprel': 'case *'},
    # 'disso': {'form': 'de isso', TODO}
    'do':      {'form': 'de o', 'lemma': 'de o'},  # 'upos': 'ADP PRON', 'deprel': 'case *''
    'dos':     {'form': 'de os', 'lemma': 'de o'},
    'na':      {'form': 'em a', 'lemma': 'em o'},
    'nesta':   {'form': 'em esta', 'lemma': 'em este'},
    'no':      {'form': 'em o', 'lemma': 'em o'},
    'nos':     {'form': 'em os', 'lemma': 'em o'},
    'numa':    {'form': 'em uma', 'lemma': 'em um'},
    'pelos':   {'form': 'por os', 'lemma': 'por o'},
    'pelo':    {'form': 'por o', 'lemma': 'por o'},
}

# shared values for all entries in MWTS
for v in MWTS.values():
    if not v.get('upos'):
        v['upos'] = 'ADP DET'
    if not v.get('deprel'):
        v['deprel'] = 'case det'
    v['feats'] = '_ *'
    # The following are the default values
    # v['main'] = 0 # which of the two words will inherit the original children (if any)
    # v['shape'] = 'siblings', # the newly created nodes will be siblings


class AddMwt(udapi.block.ud.addmwt.AddMwt):
    """Detect and mark MWTs (split them into words and add the words to the tree)."""

    def multiword_analysis(self, node):
        """Return a dict with MWT info or None if `node` does not represent a multiword token."""
        analysis = MWTS.get(node.form.lower(), None)
        if analysis is not None:
            return analysis

        if node.form.lower().endswith('-se') and node.upos == 'VERB':
            return {
                'form': node.form.lower()[:-3] + ' se',
                'lemma': '* se',
                'upos': '* PRON',
                'feats': '* _',
                'deprel': '* nsubj',  # or '* expl'
                'main': 0,
                'shape': 'subtree',
            }
        return None
