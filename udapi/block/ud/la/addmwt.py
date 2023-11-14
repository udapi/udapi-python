""" Block ud.la.AddMwt for heuristic detection of multi-word (PRON + cum, nonne) and abbreviations-dots tokens. """
import udapi.block.ud.addmwt

MWTS = {
    'mecum':   {'lemma': 'ego cum', 'form': 'me cum', 'feats': 'Case=Abl|Gender=Masc|Number=Sing AdpType=Post|Clitic=Yes'},
    'tecum':  {'lemma': 'tu cum', 'form': 'te cum', 'feats': 'Case=Abl|Gender=Masc|Number=Sing AdpType=Post|Clitic=Yes'},
    'nobiscum':   {'lemma': 'nos cum', 'form': 'nobis cum', 'feats': 'Case=Abl|Gender=Neut|Number=Plur AdpType=Post|Clitic=Yes'},
    'vobiscum': {'lemma': 'vos cum', 'form': 'vobis cum', 'feats': 'Case=Abl|Gender=Masc|Number=Plur AdpType=Post|Clitic=Yes'},
    'uobiscum': {'lemma': 'uos cum', 'form': 'uobis cum', 'feats': 'Case=Abl|Gender=Masc|Number=Plur AdpType=Post|Clitic=Yes'},
    'secum': {'lemma': 'sui cum', 'form': 'se cum', 'feats': 'Case=Abl|Gender=Masc AdpType=Post|Clitic=Yes'}, # can be singular or plural
}

# shared values for all entries in MWTS
for v in MWTS.values():
    v['upos'] = 'PRON ADP'
    # v['xpos'] = '' # treebank-specific
    v['deprel'] = 'obl case'
    v['main'] = 0
    v['shape'] = 'subtree'
	   

class AddMwt(udapi.block.ud.addmwt.AddMwt):
    """Detect and mark MWTs (split them into words and add the words to the tree)."""

    def multiword_analysis(self, node):
        """Return a dict with MWT info or None if `node` does not represent a multiword token."""
        analysis = MWTS.get(node.form.lower(), None)
        if analysis is not None:
            return analysis
            
        if node.form.endswith('.') and len(node.form) > 1 and node.form != '...':
            dic = {
                'form': 'x .',
                'lemma': '* .',
                'upos': '* PUNCT',
                'xpos': '_ _',
                'feats': '* _',
                'deprel': '* punct',
                'main': 0,
                'shape': 'subtree'
            }
            forma = node.form[:-1] + ' .'
            dic.update(form = forma)
            return dic
        elif node.lemma == 'nonne':
        	dic = {
        	'form': 'non ne',
                'lemma': 'non ne',
                'upos': 'PART PART',
                # 'xpos': '_ _', # treebank-specific
                'feats': 'Polarity=Neg Clitic=Yes|PartType=Int',
                'deprel': 'advmod:neg discourse',
                'main': 0,
                'shape': 'sibling'
        	}
        	return dic
        return None

