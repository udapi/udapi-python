import logging

from udapi.block.zellig_harris.enhancedeps import *


def en_verb_finite_form_YN(node):
    '''
    Says whether whether a verb node has finite form,
    taking into account analytical verb forms,
    unlike UD tagset.
    :param node:
    :return: boolean
    '''

    if node.upos != 'VERB':
        raise ValueError('Is not a verb.')

    if node.feats['VerbForm'] == 'Fin':
        return True

    if node.feats['VerbForm'] not in ['Inf', 'Part', 'Ger']:
        raise ValueError('Unexpected VerbForm.')

    if node.deprel == 'xcomp':
        return True

    echildren_list = echildren(node)
    for echild in echildren_list:
        if echild.upos == 'AUX':
            return True

    return False


def en_verb_passive_form_YN(node):
    '''
    Says
    :param node:
    :return: boolean
'''

    if node.upos != 'VERB':
        raise ValueError('Is not a verb.')

    if node.feats['Voice'] == 'Pass':
        return True

    if node.feats['VerbForm'] == 'Part' and node.feats['Tense'] == 'Past':
        return True

    return False
