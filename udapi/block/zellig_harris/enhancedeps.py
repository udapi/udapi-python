#!/usr/bin/env python

import logging

from udapi.core.block import Block


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
    for candidate_eparent in node.parent.children:
        if candidate_eparent.deprel == 'conj':
            final_eparents.append(candidate_eparent)

    return final_eparents

# Vincent's original function
# def echildren(node):
#     """
#     Return a list with node's effective children.
#
#     :param node: An input node.
#     :return: A list with node's effective children.
#     :rtype: list
#
#     """
#     node_parents = eparents(node)
#     echildren_list = [child for child in node.children]
#
#     # Rule (A)
#     target_deprels = ['subj', 'subjpass', 'dobj', 'iobj', 'compl']
#     for node_parent in node_parents:
#         for candidate_child in node_parent.children:
#             # Check if a candidate node C has the target deprel.
#             if candidate_child.deprel not in target_deprels:
#                 continue
#
#             # Check if such deprel is not in the current node children already.
#             no_such_deprel = True
#             for current_child in node.children:
#                 if current_child.deprel == candidate_child.deprel:
#                     no_such_deprel = False
#                     break
#
#             # If there is no such deprel, we can add a new secondary dependence.
#             if no_such_deprel:
#                 echildren_list.append(candidate_child)
#
#     # Rule (B)
#     for node_parent in node_parents:
#         if node.upostag == 'VERB' and (node_parent.upostag == 'AUX' or node_parent.lemma in ['chtít', 'moci', 'smět', 'mít', 'muset', 'umět']):
#             for candidate_child in node_parent.children:
#                 # Check if the candidate child is not in the current node children already.
#                 if candidate_child not in echildren_list:
#                     echildren_list.append(candidate_child)
#
#     return echildren_list

#Silvie's function, please check
def true_deprel(node):
    '''
    for conjunct nodes (second+ coordination members):
    Function gets deprel of the first coordination member
    :param node:
    :return: string
    '''
    truedep = node.deprel
    if node.deprel != 'conj':
        truedep = node.deprel
    mynodes_parent = node.parent
    truedep = mynodes_parent.deprel
    return truedep

#Silvie's function, please check
def shared_children(node):
    '''
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
    '''
    if node.deprel != 'conj':
        raise ValueError('Node is not a conjunct.')

    mynodes_parent = node.parent
    sharechild_candidates = mynodes_parent.children
    if len(sharechild_candidates) == 0:
        raise ValueError('No candidates for shared children.')

    for candidate in sharechild_candidates:
        if candidate.ord > mynodes_parent.ord:
            sharechild_candidates.remove(candidate) # eliminates 'in the morning' from
            # John sings *in the morning* and never dances.

    if len(sharechild_candidates) == 0:
        raise ValueError('No shared children.')

    mynodes_children = node.children
    mynodes_children_true_deprels = []
    for mynodes_child in mynodes_children:
        true_mynodes_child_deprel = true_deprel(mynodes_child)
        mynodes_children_true_deprels.append(true_mynodes_child_deprel) #List of true deprels of my node's children

    for candidate in sharechild_candidates:
        if true_deprel(candidate) in mynodes_children_true_deprels \
                and true_deprel(candidate) in ['nsubj', 'nsubjpass',
                                          'dobj', 'iobj', 'csubj',
                                          'csubjpass', 'goeswith',
                                          'mwe', 'compound', 'list',
                                          'dislocated', 'parataxis',
                                          'remnant', 'reparandum',
                                          'cc', 'conj']: # we deliberately ignore second+ conjuncts of shared children
            # i.e. from "John and Mary dance and sing", we will only find "John" as subject of "sing".
            sharechild_candidates.remove(candidate)
    if len(sharechild_candidates) == 0:
        raise ValueError('No shared children.')
    return sharechild_candidates

# Silvie's function, please check
# def  echildren(node):
#     '''
#     Gets all descendants of a node that are either its children or conjuncts of its children.
#     Just one level down, no recursivity, as UD do not support nested coordinations anyway.
#     :param node:
#     :return:
#     '''
#     if node.deprel != 'conj':
#         immediate_children_list = node.children
#         all_children_list = immediate_children_list
#         for imchild in immediate_children_list:
#             descendants_list = imchild.children
#         for descendant in descendants_list:
#             if descendant.deprel == 'conj':
#                 all_children_list.append(descendant)
#     if len(all_children_list) == 0:
#         raise ValueError('No echildren.')
#     return all_children_list
#     #  now if my node's deprel is conj
#     mynode_parent = node.parent
#     immediate_children_list = mynode_parent.children
#     for imchild in immediate_children_list: # exclude node
#         if imchild == node:
#             continue
#         descendants_list = imchild.children
#     for descendant in descendants_list:
#         if descendant.deprel == 'conj':
#                 all_children_list.append(descendant)
#     if len(all_children_list) == 0:
#         raise ValueError('No echildren.')
#     return all_children_list


def  echildren(node):
    '''
    Gets all descendants of a node that are either its children or conjuncts of its children.
    Just one level down, no recursivity, as UD do not support nested coordinations anyway.
    :param node:
    :return:
    '''
    if node.deprel != 'conj':
        target = node
    if node.deprel == 'conj':
        target = node.parent
    immediate_children_list = target.children
    all_children_list = immediate_children_list
    for imchild in immediate_children_list:
        descendants_list = imchild.children
        if imchild == target:
            continue
            descendants_list = imchild.children
        for descendant in descendants_list:
            if descendant.deprel == 'conj':
                all_children_list.append(descendant)
    if len(all_children_list) == 0:
        raise ValueError('No echildren.')
    # for child in all_children_list:
    #     print(child.lemma)
    return all_children_list




def en_verb_controller_YN(node):
    '''
    Tells whether the input verb node controls another verb
    :param node:
    :return: boolean
    '''
    if node.upostag != 'VERB':
        raise ValueError('Is not a verb.')
    result = False
    verb_echildren_list = echildren(node)
    for verb_echild in verb_echildren_list:
        if true_deprel(verb_echild) == 'xcomp':
            result = True
            break
    return result

def en_verb_controllee_YN(node):
    '''
    Tells whether the input verb is a controlled verb
    :param node:
    :return: boolean
    '''
    if node.upostag != 'VERB':
        raise ValueError('Is not a verb.')
    result = False
    if true_deprel(node) == 'xcomp':
        result = True
    return result






















def enhance_deps(node, new_dependence):
    """
    Add a new dependence to the node.deps, but firstly check
    if there is no such dependence already.

    :param node: A node to be enhanced.
    :param new_dependence: A new dependence to be add into node.deps.

    """
    for existing_dependence in node.deps:
        if existing_dependence['parent'] == new_dependence['parent'] and \
           existing_dependence['deprel'] == new_dependence['deprel']:
            return

    node.deps.append(new_dependence)


class EnhanceDeps(Block):
    """
    Identify new relations between nodes in the dependency tree (an analogy of effective parents/children from PML).
    Add these new relations into secondary dependencies slot.

    """

    def __init__(self, args=None):
        """
        Initialization.

        :param args: A dict of optional parameters.

        """
        super(Block, self).__init__()

        if args is None:
            args = {}

    def process_node(self, node):
        """
        Enhance secondary dependencies by application of the following rules:
        1. when the current node A has a deprel 'conj' to its parent B, create a new secondary dependence
           (B.parent, B.deprel) to A
        2. when the current node A has a deprel 'conj' to its parent B, look at B.children C
           when C.deprel is in {subj, subjpass, iobj, dobj, compl} and there is no A.children D
           such that C.deprel == D.deprel, add a new secondary dependence (A, C.deprel) to C

        :param node: A node to be process.

        """
        # Both rules require node.deprel to be 'conj'.
        if node.deprel != 'conj':
            return

        # Node's parent should not be root.
        if node.parent.is_root():
            return

        # Apply rule (1)
        enhance_deps(node, {'parent': node.parent.parent, 'deprel': node.parent.deprel})

        # Apply rule (2)
        target_deprels = ['subj', 'subjpass', 'dobj', 'iobj', 'compl']
        for candidate_child in node.parent.children:
            # Check if a candidate node C has the target deprel.
            if candidate_child.deprel not in target_deprels:
                continue

            # Check if such deprel is not in the current node children already.
            no_such_deprel = True
            for current_child in node.children:
                if current_child.deprel == candidate_child.deprel:
                    no_such_deprel = False
                    break

            # If there is no such deprel, we can add a new secondary dependence.
            if no_such_deprel:
                enhance_deps(candidate_child, {'parent': node, 'deprel': candidate_child.deprel})

def en_verb_finite_form_YN(node):
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


def en_verb_passive_form_YN(node):
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



