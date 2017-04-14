#!/usr/bin/env python

from udapi.core.block import Block
from udapi.block.zellig_harris.morphotests import *


eparent_echildren_deprels = ['nsubj', 'nsubjpass', 'dobj', 'iobj', 'csubj', 'csubjpass', 'goeswith', 'mwe',
                             'compound', 'list', 'dislocated', 'parataxis', 'remnant', 'reparandum', 'cc', 'conj']


def eparents(node):
    """
    Return a list of effective parents for the given node.

    :param node: An input node.
    :return: A list of effective parents.
    :rtype: list

    """
    # Rule (1): When node.deprel == conj, its effective parents are equal to its parent.
    if node.deprel == 'conj':
        return eparents(node.parent)

    # Rule (2): Append the real parent and look for its coordinated nodes.
    final_eparents = [node.parent]
    node_true_deprel = true_deprel(node)
    for candidate_eparent in node.parent.children:
        if candidate_eparent.deprel == 'conj':
            if node_true_deprel in eparent_echildren_deprels:
                if node_true_deprel in [node.deprel for node in candidate_eparent.children]:
                    continue

            final_eparents.append(candidate_eparent)

    return final_eparents


def true_deprel(node):
    """
    for conjunct nodes (second+ coordination members):
    Function gets deprel of the first coordination member
    :param node:
    :return: string
    """
    if node.deprel != 'conj':
        return node.deprel

    return true_deprel(node.parent)


def schildren(node):
    """
    If the input node is a second+ member of a coordination (deprel 'conj'),
    the function will return a list of modifiers of its immediate parent
    (the first coordination member).
    Example: 'John will sing and dance': 'John' is shared child of 'dance'.
    Children of the first coordination member that are to the right of it
    are ignored. Example: 'John will sing at performances and dance'. At performances
     will not be recorded as a shared child of dance.
     Left-hand-side children of the first coordination member that are subject, object
     or 'complicated' elements, such as list mwe, cc, and conj, are not recorded as shared children
     of the conjunct when the conjunct has its own child with the same deprel.
    :param node:
    :return: list
    """
    if node.deprel != 'conj':
        return []

    mynodes_parent = node.parent
    sharechild_candidates = mynodes_parent.children

    # Eliminating candidates according to their ordering.
    for candidate in sharechild_candidates:
        if mynodes_parent.ord < candidate.ord < node.ord:
            sharechild_candidates.remove(candidate) # eliminates 'in the morning' from
            # John sings *in the morning* and never dances.

    mynodes_children = node.children
    mynodes_children_true_deprels = []
    for mynodes_child in mynodes_children:
        true_mynodes_child_deprel = true_deprel(mynodes_child)
        mynodes_children_true_deprels.append(true_mynodes_child_deprel) #List of true deprels of my node's children

    for candidate in sharechild_candidates:
        if true_deprel(candidate) in mynodes_children_true_deprels \
                and true_deprel(candidate) in eparent_echildren_deprels: # we deliberately ignore second+ conjuncts of
            # shared children
            # i.e. from "John and Mary dance and sing", we will only find "John" as subject of "sing".
            sharechild_candidates.remove(candidate)

    return sharechild_candidates


def echildren(node):
    """
    Gets all descendants of a node that are either its children or conjuncts of its children.
    Just one level down, no recursivity, as UD do not support nested coordinations anyway.

    :param node: An input node.
    :return: A list of node's effective children.

    """
    echildren_list = []
    for real_child in node.children:
        if real_child.deprel != 'conj':
            echildren_list.append(real_child)

        for child in real_child.children:
            if child.deprel == 'conj':
                echildren_list.append(child)

    return echildren_list


def eschildren(node):
    """
    Obtain echildren, schildren and combine them into one list.

    :param node: An input nude.
    :return: list

    """
    output_list = echildren(node)
    for schild in schildren(node):
        if schild in output_list:
            raise ValueError('Shared child appears in echildren list: %r', schild)

        output_list.append(schild)

    return output_list


def en_verb_controller_YN(node):
    """
    Tells whether the input verb node controls another verb

    :param node: An input node.
    :return: boolean

    """
    if node.upos != 'VERB':
        raise ValueError('Is not a verb.')
    result = False
    verb_echildren_list = echildren(node)
    for verb_echild in verb_echildren_list:
        if true_deprel(verb_echild) == 'xcomp':
            result = True
            break
    return result


def en_verb_controllee_YN(node):
    """
    Tells whether the input verb is a controlled verb

    :param node: An input node.
    :return: boolean

    """
    if node.upos != 'VERB':
        raise ValueError('Is not a verb.')
    result = False
    if true_deprel(node) == 'xcomp':
        result = True
    return result


def en_verb_finite_form_YN(node):
    """
    Says whether whether a verb node has finite form,
    taking into account analytical verb forms,
    unlike UD tagset.

    :param node: An input node.
    :return: boolean

    """
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
    """
    Says

    :param node: An input node.
    :return: boolean

    """
    if node.upos != 'VERB':
        raise ValueError('Is not a verb.')

    if node.feats['Voice'] == 'Pass':
        return True

    if node.feats['VerbForm'] == 'Part' and node.feats['Tense'] == 'Past':
        return True



