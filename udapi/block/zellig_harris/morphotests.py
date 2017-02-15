from udapi.block.zellig_harris.enhancedeps import *

def en_finite_verbform(node):
    '''
    Says whether whether a verb node has finite form,
    taking into account analytical verb forms,
    unlike UD tagset.
    :param node:
    :return: boolean
    '''
    if node.upostag != 'VERB':
        raise ValueError('Is not a verb.')

    if node.feats.get('VerbForm', '') == 'Fin':
        return True


    if node.feats.get('VerbForm', '') not in ['Inf', 'Part', 'Ger']:
        raise ValueError('Unexpected VerbForm.')

    if node.deprel == 'xcomp':
        return True

    echildren_list = echildren(node)
    for echild in echildren_list:
        if echild.upostag == 'AUX':
            return True

    return False


def en_passive_verbform(node):
    '''
    Says
    :param node:
    :return: boolean
    '''

    if node.upostag != 'VERB':
        raise ValueError('Is not a verb.')
    if node.feats.get('Voice', '') == 'Pass':
        return True

    if node.feats.get('VerbForm', '') == 'Part' and node.feats.get('Tense', '') == 'Past':
        return True










