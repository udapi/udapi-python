"""Block ud.ga.To2 UD_Irish-specific conversion of UDv1 to UDv2

Author: Martin Popel
"""
from udapi.core.block import Block


class To2(Block):
    """Block for fixing the remaining cases (after ud.Convert1to2) in UD_Irish."""

    # pylint: disable=too-many-branches
    def process_node(self, node):
        if node.feats['Case'] == 'Com':
            node.feats['Case'] = 'NomAcc'
        if node.feats['Form'] == 'Emph':
            if node.upos in ('PRON', 'ADP'):
                node.feats['PronType'] = 'Emp'
                del node.feats['Form']
            else:
                node.feats['Form'] = 'Emp'
        if node.deprel == 'nmod:prep':
            node.deprel = 'obl:prep'
        if node.deprel == 'nmod:tmod':
            node.deprel = 'obl:tmod'
        if node.xpos == 'Abr':
            node.feats['Abbr'] = 'Yes'
        if node.xpos == 'Cop':
            node.upos = 'AUX'
        if node.xpos == 'Foreign':
            node.feats['Foreign'] = 'Yes'
        if 'nmod' in node.misc['ToDo']:
            del node.misc['ToDo']

        if node.feats['VerbForm'] in ('Inf', 'Vnoun', 'Ger'):
            if node.prev_node.lemma == 'ag' and node.prev_node.parent == node:
                node.feats['VerbForm'] = 'Vnoun'
            else:
                node.feats['VerbForm'] = 'Inf'
