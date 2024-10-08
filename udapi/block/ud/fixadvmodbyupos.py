"""
Block ud.FixAdvmodByUpos will change the dependency relation from advmod to something else
if the UPOS is not ADV.
"""
from udapi.core.block import Block


class FixAdvmodByUpos(Block):
    """
    Make sure advmod is not used with UPOS it should not be used with.
    """

    def process_node(self, node):
        if node.udeprel == 'advmod':
            if node.upos in ['NOUN', 'PROPN', 'PRON', 'DET', 'NUM']:
                node.deprel = 'obl'
            elif node.upos == 'VERB':
                node.deprel = 'advcl'
            elif node.upos == 'AUX':
                node.deprel = 'aux'
            elif node.upos in ['ADP', 'SCONJ']:
                if node.parent.upos == 'VERB':
                    node.deprel = 'mark'
                else:
                    node.deprel = 'case'
            elif node.upos == 'CCONJ':
                node.deprel = 'cc'
            elif node.upos == 'INTJ':
                node.deprel = 'discourse'
            else:
                node.deprel = 'dep'
        ###!!! The following are not advmod so they should probably have their
        ###!!! own block or this block should have a different name.
        elif node.udeprel == 'expl':
            if node.upos == 'AUX':
                node.deprel = 'aux'
        elif node.udeprel == 'mark':
            if node.upos == 'PRON':
                node.deprel = 'nsubj' # it could be also obj, iobj, obl or nmod; just guessing what might be more probable
        elif node.udeprel == 'det':
            if node.upos == 'ADJ':
                node.deprel = 'amod'
