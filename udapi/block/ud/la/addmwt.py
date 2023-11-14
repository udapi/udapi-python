""" Block ud.la.AddMwt for heuristic detection of multi-word (PRON + cum, nonne) and abbreviations-dots tokens. """
import udapi.block.ud.addmwt

MWTS = {
    'mecum':   {'lemma': 'ego cum', 'form': 'me cum', 'upos': 'PRON ADP', 'feats': 'Case=Abl|Gender=Masc|Number=Sing AdpType=Post|Clitic=Yes', 'deprel': 'obl case'},
    'tecum':  {'lemma': 'tu cum', 'form': 'te cum', 'upos': 'PRON ADP', 'feats': 'Case=Abl|Gender=Masc|Number=Sing AdpType=Post|Clitic=Yes', 'deprel': 'obl case'},
    'nobiscum':   {'lemma': 'nos cum', 'form': 'nobis cum', 'upos': 'PRON ADP', 'feats': 'Case=Abl|Gender=Neut|Number=Plur AdpType=Post|Clitic=Yes', 'deprel': 'obl case'},
    'vobiscum': {'lemma': 'vos cum', 'form': 'vobis cum', 'upos': 'PRON ADP', 'feats': 'Case=Abl|Gender=Masc|Number=Plur AdpType=Post|Clitic=Yes', 'deprel': 'obl case'},
    'uobiscum': {'lemma': 'uos cum', 'form': 'uobis cum', 'upos': 'PRON ADP', 'feats': 'Case=Abl|Gender=Masc|Number=Plur AdpType=Post|Clitic=Yes', 'deprel': 'obl case'},
    'secum': {'lemma': 'sui cum', 'form': 'se cum', 'upos': 'PRON ADP', 'feats': 'Case=Abl|Gender=Masc AdpType=Post|Clitic=Yes', 'deprel': 'obl case'}, # can be singular or plural
    'nonne': {'lemma': 'non ne', 'form': 'non ne', 'upos': 'PART PART', 'feats': 'Polarity=Neg Clitic=Yes|PartType=Int', 'deprel': 'advmod:neg discourse', 'shape': 'sibling'}
}

# shared values for all entries in MWTS
for v in MWTS.values():
    # v['xpos'] = '' # treebank-specific
    if 'shape' not in v:
        v['shape'] = 'subtree'
    v['main'] = 0
	   

class AddMwt(udapi.block.ud.addmwt.AddMwt):
    """Detect and mark MWTs (split them into words and add the words to the tree)."""

    def multiword_analysis(self, node):
        """Return a dict with MWT info or None if `node` does not represent a multiword token."""
        analysis = MWTS.get(node.form.lower(), None)
        if analysis is not None:
            return analysis
            
        if node.form.endswith('.') and len(node.form) > 1 and node.form != '...':
	    # currently under discussion
            return {'form': node.form[:-1] + ' .',
                'lemma': '* .',
                'upos': '* PUNCT',
                'xpos': '_ _',
                'feats': '* _',
                'deprel': '* punct',
                'main': 0,
                'shape': 'subtree'}

