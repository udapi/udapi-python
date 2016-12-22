import logging


def en_verb_mydobj(node):
    """
    Extract the 'myobj' relation.

    """
    if node.upostag != 'VERB':
        raise ValueError('Is not a verb.')

    if node.feats.get('Tense', '') != 'Past':
        raise ValueError('Is not in the past tense.')

    if node.feats.get('VerbForm', '') != 'Part':
        raise ValueError('Is not in a participle form.')

    triples = []
    for child_node in node.children:
        if child_node.deprel != 'dobj':
            continue

        if child_node.ord > node.ord:
            triples.append((node, 'dobj', child_node))

    return triples
