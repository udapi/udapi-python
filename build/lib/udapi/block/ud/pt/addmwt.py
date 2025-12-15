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
    'ao':      {'form': 'a o', 'lemma': 'a o'},
    'aos':     {'form': 'a os', 'lemma': 'a o'},
    'da':      {'form': 'de a', 'lemma': 'de o'},
    'das':     {'form': 'de as', 'lemma': 'de o'},
    'dessa':   {'form': 'de essa', 'lemma': 'de esse'},
    'dessas':  {'form': 'de essas', 'lemma': 'de esse'},
    'desse':   {'form': 'de esse', 'lemma': 'de esse'},
    'desses':  {'form': 'de esses', 'lemma': 'de esse'},
    'desta':   {'form': 'de esta', 'lemma': 'de este'},
    'destas':  {'form': 'de estas', 'lemma': 'de este'},
    'deste':   {'form': 'de este', 'lemma': 'de este'},
    'destes':  {'form': 'de estes', 'lemma': 'de este'},
    'disso':   {'form': 'de isso', 'lemma': 'de este'},
    'disto':   {'form': 'de isto', 'lemma': 'de este'},
    'do':      {'form': 'de o', 'lemma': 'de o'},  # 'upos': 'ADP PRON', 'deprel': 'case *''
    'dos':     {'form': 'de os', 'lemma': 'de o'},
    'dum':     {'form': 'de um', 'lemma': 'de um'},
    'duma':    {'form': 'de uma', 'lemma': 'de um'},
    'dumas':   {'form': 'de umas', 'lemma': 'de um'},
    'duns':    {'form': 'de uns', 'lemma': 'de um'},
    'na':      {'form': 'em a', 'lemma': 'em o'},
    'nas':     {'form': 'em as', 'lemma': 'em o'},  # ADP PRON
    'nesses':  {'form': 'em esses', 'lemma': 'em esse'},
    'nesta':   {'form': 'em esta', 'lemma': 'em este'},
    'neste':   {'form': 'em este', 'lemma': 'em este'},
    'nisso':   {'form': 'em isso', 'lemma': 'em este'},
    'nisto':   {'form': 'em isto', 'lemma': 'em este',
                'upos': 'ADP PRON', 'main': 1, 'shape': 'subtree'},
    'no':      {'form': 'em o', 'lemma': 'em o'}, # PRON cases are excluded below
    'nos':     {'form': 'em os', 'lemma': 'em o'}, # PRON cases are excluded below
    'num':     {'form': 'em um', 'lemma': 'em um'},
    'numa':    {'form': 'em uma', 'lemma': 'em um'},
    'numas':   {'form': 'em umas', 'lemma': 'em um'},
    'nuns':    {'form': 'em uns', 'lemma': 'em um'},
    'pela':    {'form': 'por a', 'lemma': 'por o'},
    'pelas':   {'form': 'por as', 'lemma': 'por o'},
    'pelos':   {'form': 'por os', 'lemma': 'por o'},
    'pelo':    {'form': 'por o', 'lemma': 'por o'},
    # TODO daí = de aí = ADP ADV = case advmod
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

for pronoun in 'ela ele eles elas'.split():
    MWTS['d' + pronoun] = {
        'form': 'de ' + pronoun,
        'lemma': 'de ' + pronoun,
        'upos': 'ADP PRON',
        'deprel': 'case *',
        'main': 1,
        'shape': 'subtree',
    }


class AddMwt(udapi.block.ud.addmwt.AddMwt):
    """Detect and mark MWTs (split them into words and add the words to the tree)."""

    def multiword_analysis(self, node):
        """Return a dict with MWT info or None if `node` does not represent a multiword token."""

        # "no" can be either a contraction of "em o", or a pronoun
        if node.form.lower() in ('no', 'nos') and node.upos == 'PRON':
            return

        analysis = MWTS.get(node.form.lower(), None)

        # If the input is e.g.:
        # 1   na      _ ADP  _ _ deprel_x ?
        # 2   verdade _ NOUN _ _ fixed    1
        # The expected output is:
        # 1-2 na      _ _    _ _ _        _
        # 1   em      _ ADP  _ _ deprel_x ?
        # 2   a       _ DET  _ _ fixed    1
        # 3   verdade _ NOUN _ _ fixed    1
        if analysis and analysis['deprel'] == 'case det' and node.udeprel != 'case':
            copy = dict(analysis)
            copy['deprel'] = '* det'
            copy['shape'] = 'subtree'
            first_child = next((c for c in node.children if node.precedes(c)), None)
            if first_child is not None and first_child.udeprel == 'fixed':
                copy['deprel'] = '* fixed'
            return copy
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
        elif node.form.lower().endswith('-lo') and node.upos == 'VERB':
            return {
                'form': node.form.lower()[:-3] + ' lo',
                'lemma': '* ele',
                'upos': '* PRON',
                'feats': '* _',
                'deprel': '* obj',
                'main': 0,
                'shape': 'subtree',
            }
        elif node.form.lower().endswith('-los') and node.upos == 'VERB':
            return {
                'form': node.form.lower()[:-4] + ' los',
                'lemma': '* eles',
                'upos': '* PRON',
                'feats': '* _',
                'deprel': '* obj',
                'main': 0,
                'shape': 'subtree',
            }
        elif node.form.lower().endswith('-o') and node.upos == 'VERB':
            return {
                'form': node.form.lower()[:-2] + ' o',
                'lemma': '* ele',
                'upos': '* PRON',
                'feats': '* _',
                'deprel': '* obj',
                'main': 0,
                'shape': 'subtree',
            }
        return None
