import logging
from udapi.block.zellig_harris.enhancedeps import *
# from udapi.block.zellig_harris.morphotests import *
import udapi.block.zellig_harris.enhancedeps


# this is a mock function
# - it technically works, but linguistically it's nonsense
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
    for child_node in echildren(node):
        if child_node.deprel != 'dobj':
            continue

        if child_node.ord > node.ord:
            triples.append((node, 'dobj', child_node))

    return triples


def en_noun_is_dobj_of(node):
    """

    :param node:
    :return:
    """
    my_revert = en_verb_mydobj(node)  # pole trojic
    my_reverted = []
    for triple in my_revert:
        my_reverted.append((triple[2], triple[1], triple[0]))
    return my_reverted


# Silvie does not alter the above functions until understood how they work.
# Creating new ones instead if these work improperly.

#####Silvie's functions
def en_noun_is_subj_relcl(node):
    '''
    Extract the 'nsubj' relation from a relative clause.
    Example: the man who called me yesterday (-> 'man' is subject of 'call')
    :param node:
    :return: n-tuple containing triples
    '''
    if node.upostag not in ['PROPN', 'NOUN']:
        raise ValueError('Is not a noun.')
    mynode_echildren_list = echildren(node)
    relcl_verbs_list = []
    for mynode_echild in mynode_echildren_list:
        if true_deprel(mynode_echild) == 'acl:relcl' or mynode_echild.deprel == 'acl:relcl':
            # print('RELATIVE CLAUSE')
            relcl_verbs_list.append(mynode_echild)
    if len(relcl_verbs_list) == 0:
        raise ValueError('Not subject of any relative clause')
    for relcl_verb in relcl_verbs_list:
        if en_verb_passive_form_YN(relcl_verb):
            continue
    if len(relcl_verbs_list) == 0:
        raise ValueError('Verb in relative clause is passive')

    triples = []
    for relcl_verb in relcl_verbs_list:
        wrong_subjects_list = echildren(relcl_verb)
        for wrong_subject in wrong_subjects_list:
            if (true_deprel(wrong_subject) not in ['nsubj',
                                                   'nsubjpass',
                                                   'csubj',
                                                   'csubjpass'] \
                        or wrong_subject.deprel not in ['nsubj',
                                                        'nsubjpass',
                                                        'csubj',
                                                        'csubjpass']) \
                    and wrong_subject.lemma not in ['where',
                                                    'how',
                                                    'why',
                                                    'when']:
                wrong_subjects_list.remove(wrong_subject)

        for wrong_subject in wrong_subjects_list:
            if true_deprel(wrong_subject) in ['nsubjpass',
                                              'csubj',
                                              'csubjpass'] \
                    or wrong_subject.deprel in ['nsubjpass',
                                                'csubj',
                                                'csubjpass']:
                raise ValueError('Verb has its own regular subject - passive or clausal')

            if wrong_subject.lemma in ['where',
                                       'how',
                                       'why',
                                       'when']:
                raise ValueError('Noun is an adverbial, not subject.')


            if wrong_subject.deprel == 'nsubj' and wrong_subject.feats.get('PronType', '') != 'Rel':
               raise ValueError('Verb has its own subject.01')

            if len(wrong_subjects_list) == 0:  # NB when recycling this script for extraction of other arguments from relclauses.
                # For object relclauses the list will have to be empty of potential objects!!!
                raise ValueError('Subject-relative clause must contain a relative pronoun subject!')

        triples.append((node, 'nsubj', relcl_verb))

    return triples
