#!/usr/bin/env python

from udapi.core.block import Block


def eparent(node):
    """
    Return an effective parent for the given node.

    The rule for the effective parent - when the current node A has a deprel 'conj' to its parent B,
    return  B.parent, otherwise return A.parent.

    :param node: An input node.
    :return: An effective parent.
    :rtype: udapi.core.node.Node

    """
    if node.deprel == 'conj':
        return node.parent.parent

    return node.parent


def echildren(node):
    """
    Return a list with node's effective children.

    :param node: An input node.
    :return: A list with node's effective children.
    :rtype: list

    """
    target_deprels = ['subj', 'subjpass', 'dobj', 'iobj', 'compl']
    node_parent = eparent(node)
    echildren_list = [child for child in node.children]

    for candidate_child in node_parent.children:
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
            echildren_list.append(candidate_child)

    return echildren_list


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
    Identify new relations between nodes in the dependency tree
    (an analogy of effective parents/children from PML).
    Add these new relations into secondary dependencies slot.

    """

    def process_node(self, node):
        """
        Enhance secondary dependencies by application of the following rules:
        1. when the current node A has a deprel 'conj' to its parent B,
           create a new secondary dependence (B.parent, B.deprel) to A
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
