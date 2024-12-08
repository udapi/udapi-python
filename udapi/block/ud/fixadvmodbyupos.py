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
            elif node.upos == 'ADP':
                node.deprel = 'case'
            elif node.upos == 'CCONJ':
                node.deprel = 'cc'
        elif node.udeprel in ['aux', 'cop']:
            if node.upos != 'AUX':
                node.deprel = 'dep'
        elif node.udeprel == 'case':
            if node.upos == 'DET':
                node.deprel = 'det'
        elif node.udeprel == 'mark':
            if node.upos in ['PRON', 'DET']:
                node.deprel = 'nsubj' # it could be also obj, iobj, obl or nmod; just guessing what might be more probable
            elif node.upos == 'INTJ':
                node.deprel = 'discourse'
        elif node.udeprel == 'cc':
            if node.upos == 'AUX':
                node.deprel = 'aux'
            elif node.upos == 'DET':
                node.deprel = 'det'
            elif node.upos == 'INTJ':
                node.deprel = 'discourse'
        elif node.udeprel == 'det':
            if node.upos == 'NOUN':
                node.deprel = 'nmod'
            elif node.upos == 'ADJ':
                node.deprel = 'amod'
            elif node.upos == 'ADV':
                node.deprel = 'advmod'
            elif node.upos == 'AUX':
                node.deprel = 'aux'
            elif node.upos == 'VERB':
                node.deprel = 'dep'
            elif node.upos == 'X':
                node.deprel = 'dep'
        elif node.udeprel == 'nummod':
            if node.upos == 'PRON':
                node.deprel = 'nmod'
            elif node.upos == 'DET':
                node.deprel = 'det'
        elif node.udeprel == 'punct':
            if node.upos != 'PUNCT':
                node.deprel = 'dep'
