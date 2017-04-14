import logging

from udapi.block.zellig_harris.enhancedeps import *
from udapi.block.zellig_harris.morphotests import *

# this is a mock function
# - it technically works, but linguistically it's nonsense
def en_verb_mydobj(node):
    """
    Extract the 'myobj' relation.

    """
    if node.upos != 'VERB':
        raise ValueError('Is not a verb.')

    if node.feats['Tense'] != 'Past':
        raise ValueError('Is not in the past tense.')

    if node.feats['VerbForm'] != 'Part':
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

####Silvie's functions
def en_noun_is_subj_relcl(node):
    '''
    Extract the 'nsubj' relation from a relative clause.
    Example: the man who called me yesterday (-> 'man' is subject of 'call')
    :param node:
    :return: n-tuple containing triples
    '''

    if node.upos not in ['PROPN', 'NOUN']:
        raise ValueError('Is not a noun.')

    relcl_verbs_list = []
    mynode_echildren_list = echildren(node)
    logging.info('Echildren for node %s: %r', node, [node.form for node in mynode_echildren_list])

    for mynode_echild in mynode_echildren_list:
        if true_deprel(mynode_echild) == 'acl:relcl':
            relcl_verbs_list.append(mynode_echild)

    if len(relcl_verbs_list) == 0:
        raise ValueError('Not subject of any relative clause')

    triples = []
    for relcl_verb in relcl_verbs_list:
        # if en_verb_passive_form_YN(relcl_verb):
        #     logging.info('Passive form for candidate verb %s', relcl_verb)
        #     continue

        wrong_subjects_list = echildren(relcl_verb)
        logging.info('Candidate: %s, %r', relcl_verb, [node.form for node in wrong_subjects_list])
        for wrong_subject in wrong_subjects_list:
            if true_deprel(wrong_subject) not in ['nsubj', 'nsubjpass', 'csubj','csubjpass'] and wrong_subject.lemma not in ['where', 'how', 'why', 'when']:
                wrong_subjects_list.remove(wrong_subject)

        for wrong_subject in wrong_subjects_list:
            if true_deprel(wrong_subject) in ['nsubjpass', 'csubj', 'csubjpass']:
                raise ValueError('Verb has its own regular subject - passive or clausal')

            if wrong_subject.lemma in ['where', 'how', 'why', 'when']:
                raise ValueError('Noun is an adverbial, not subject.')

            if wrong_subject.deprel == 'nsubj' and wrong_subject.feats['PronType'] != 'Rel':
                raise ValueError('Verb has its own subject.01')

            if len(wrong_subjects_list) == 0:  # NB when recycling this script for extraction of other arguments from relclauses.
                # For object relclauses the list will have to be empty of potential objects!!!
                raise ValueError('Subject-relative clause must contain a relative pronoun subject!')

        triples.append((node, 'nsubj', relcl_verb))
        with open('C:\log_SILVIE.txt', 'a') as file:
            file.write('haha')

    return triples


"""Iveta -  en_verb_has_subject_is_relcl"""


def en_verb_has_subject_is_relcl(node):
     if node.upos != 'VERB':
         raise ValueError('It is not a verb.')
     if true_deprel(node) != 'acl:relcl':
         raise ValueError('It is not a relative clause.')
     ekids_controllees_list = []
     if en_verb_controller_YN(node):
         ekids_01_list = echildren(node)

         for ekid_01 in ekids_01_list:
             if true_deprel(ekid_01) == 'xcomp' and not (en_verb_passive_form_YN(ekid_01)):
                 ekids_controllees_list.append(ekid_01)

     ekids_list = echildren(node)
     relsubjs_list = []
     for ekid in ekids_list:
         if true_deprel(ekid) == 'nsubj' and ekid.feats['PronType'] == 'Rel':
             relsubjs_list.append(ekid)
     if len(relsubjs_list) == 0:
         raise ValueError('Relative clause, but not subject relclause.')
     epar_list = eparents(node)
     triples = []
     for epar in epar_list:
         if epar.upos in ('NOUN', 'PROPN'):
             triples.append((node, 'nsubj', epar))
             for ekid_controllee in ekids_controllees_list:
                 triples.append((ekid_controllee, 'nsubj', epar))
     return triples




def en_verb_has_iobj_is_relclActive(node):   #does not check controlled werbs
     if node.upos != 'VERB':
         raise ValueError('It is not a verb.')
     if true_deprel(node) != 'acl:relcl':
         raise ValueError('It is not a relative clause.')
     # ekids_controllees_list = []
     # if en_verb_controller_YN(node):
     #    ekids_01_list = echildren(node)

    #   for ekid_01 in ekids_01_list:
     #        if true_deprel(ekid_01) == 'xcomp' and not (en_verb_passive_form_YN(ekid_01)):
     #            ekids_controllees_list.append(ekid_01)

     ekids_list = echildren(node)
     reliobjs_list = []
     for ekid in ekids_list:
         if true_deprel(ekid) == 'iobj' and ekid.feats['PronType'] == 'Rel':
             reliobjs_list.append(ekid)
     if len(reliobjs_list) == 0:
         raise ValueError('Relative clause, but not iobject relclause.')
     epar_list = eparents(node)
     triples =[]
     for epar in epar_list:
         if epar.upos in ('NOUN', 'PROPN'):
             triples.append((node, 'iobj', epar))
         #    for ekid_controllee in ekids_controllees_list:
         #        triples.append((ekid_controllee, 'nsubj', epar))
     return triples


def en_verb_has_iobj_is_relclPassive(node):  # does not check controlled werbs
    if node.upos != 'VERB':
        raise ValueError('It is not a verb.')
    if true_deprel(node) != 'acl:relcl':
        raise ValueError('It is not a relative clause.')
        # ekids_controllees_list = []
        # if en_verb_controller_YN(node):
        #    ekids_01_list = echildren(node)

        #   for ekid_01 in ekids_01_list:
    #        if true_deprel(ekid_01) == 'xcomp' and not (en_verb_passive_form_YN(ekid_01)):
    #            ekids_controllees_list.append(ekid_01)

    ekids_list = echildren(node)
    reliobjs_list = []
    dobjs_list=[]
    for ekid in ekids_list:
        if true_deprel(ekid) == 'nsubjpass' and ekid.feats['PronType'] == 'Rel':
            reliobjs_list.append(ekid)
        if true_deprel(ekid) in ['dobj','ccomp','xcomp']:
            dobjs_list.append(ekid)
    if len(reliobjs_list) == 0:
        raise ValueError('Relative clause, but not obj relclause.')
    if len(dobjs_list) ==0:
        raise ValueError('Is not indirect object.')
    epar_list = eparents(node)
    triples = []
    for epar in epar_list:
        if epar.upos in ('NOUN', 'PROPN'):
            triples.append((node, 'iobj', epar))
            #    for ekid_controllee in ekids_controllees_list:
            #        triples.append((ekid_controllee, 'nsubj', epar))
    return triples




def en_verb_has_dobj_is_relclPassive(node):  # does not check controlled werbs
    if node.upos != 'VERB':
        raise ValueError('It is not a verb.')
    if true_deprel(node) != 'acl:relcl':
        raise ValueError('It is not a relative clause.')
        # ekids_controllees_list = []
        # if en_verb_controller_YN(node):
        #    ekids_01_list = echildren(node)

        #   for ekid_01 in ekids_01_list:
    #        if true_deprel(ekid_01) == 'xcomp' and not (en_verb_passive_form_YN(ekid_01)):
    #            ekids_controllees_list.append(ekid_01)

    ekids_list = echildren(node)
    reldobjs_list = []
    dobjs_list=[]
    for ekid in ekids_list:
        if true_deprel(ekid) == 'nsubjpass' and ekid.feats['PronType'] == 'Rel':
            reldobjs_list.append(ekid)
        if true_deprel(ekid) in ['dobj','ccomp','xcomp']:
            dobjs_list.append(ekid)
    if len(reldobjs_list) == 0:
        raise ValueError('Relative clause, but not obj relclause.')
    if len(dobjs_list) !=0:
        raise ValueError('Is not direct object.')
    epar_list = eparents(node)
    triples = []
    for epar in epar_list:
        if epar.upos in ('NOUN', 'PROPN'):
            triples.append((node, 'iobj', epar))
            #    for ekid_controllee in ekids_controllees_list:
            #        triples.append((ekid_controllee, 'nsubj', epar))
    return triples





def en_verb_has_dobj_is_relclActive(node):  # does not check controlled werbs
    if node.upos != 'VERB':
        raise ValueError('It is not a verb.')
    if true_deprel(node) != 'acl:relcl':
        raise ValueError('It is not a relative clause.')
        # ekids_controllees_list = []
        # if en_verb_controller_YN(node):
        #    ekids_01_list = echildren(node)

        #   for ekid_01 in ekids_01_list:
    #        if true_deprel(ekid_01) == 'xcomp' and not (en_verb_passive_form_YN(ekid_01)):
    #            ekids_controllees_list.append(ekid_01)
    active=False
    ekids_list = echildren(node)
    for ekid in ekids_list:
        if true_deprel(ekid) == 'nsubj':
            active=True;
        if true_deprel(ekid) == 'nsubj' and ekid.feats['PronType'] == 'Rel':
            raise ValueError('It is a subject clause.')
        if (true_deprel(ekid) == 'dobj' and not(ekid.feats['PronType'] == 'Rel')):
            raise ValueError('Is not direct object.')

    if not active:
        raise ValueError('Verb is not active')

    epar_list = eparents(node)
    triples = []
    for epar in epar_list:
        if epar.upos in ('NOUN', 'PROPN'):
            triples.append((node, 'dobj', epar))
            #    for ekid_controllee in ekids_controllees_list:
            #        triples.append((ekid_controllee, 'nsubj', epar))
    return triples









