import logging

from udapi.block.zellig_harris.enhancedeps import *
from udapi.block.zellig_harris.morphotests import *
from udapi.core.node import *
from udapi.block.zellig_harris.derinet import *
from udapi.block.zellig_harris.evaluation import *

der = Derinet()
eval = Evaluation()

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
# def en_noun_is_subj_relcl(node):
#     '''
#     Extract the 'nsubj' relation from a relative clause.
#     Example: the man who called me yesterday (-> 'man' is subject of 'call')
#     :param node:
#     :return: n-tuple containing triples
#     '''
#
#     if node.upos not in ['PROPN', 'NOUN']:
#         raise ValueError('Is not a noun.')
#
#     relcl_verbs_list = []
#     mynode_echildren_list = echildren(node)
#     logging.info('Echildren for node %s: %r', node, [node.form for node in mynode_echildren_list])
#
#     for mynode_echild in mynode_echildren_list:
#         if true_deprel(mynode_echild) == 'acl:relcl':
#             relcl_verbs_list.append(mynode_echild)
#
#     if len(relcl_verbs_list) == 0:
#         raise ValueError('Not subject of any relative clause')
#
#     triples = []
#     for relcl_verb in relcl_verbs_list:
#         # if en_verb_passive_form_YN(relcl_verb):
#         #     logging.info('Passive form for candidate verb %s', relcl_verb)
#         #     continue
#
#         wrong_subjects_list = echildren(relcl_verb)
#         logging.info('Candidate: %s, %r', relcl_verb, [node.form for node in wrong_subjects_list])
#         for wrong_subject in wrong_subjects_list:
#             if true_deprel(wrong_subject) not in ['nsubj', 'nsubjpass', 'csubj','csubjpass'] and wrong_subject.lemma not in ['where', 'how', 'why', 'when']:
#                 wrong_subjects_list.remove(wrong_subject)
#
#         for wrong_subject in wrong_subjects_list:
#             if true_deprel(wrong_subject) in ['nsubjpass', 'csubj', 'csubjpass']:
#                 raise ValueError('Verb has its own regular subject - passive or clausal')
#
#             if wrong_subject.lemma in ['where', 'how', 'why', 'when']:
#                 raise ValueError('Noun is an adverbial, not subject.')
#
#             if wrong_subject.deprel == 'nsubj' and wrong_subject.feats['PronType'] != 'Rel':
#                 raise ValueError('Verb has its own subject.01')
#
#             if len(wrong_subjects_list) == 0:  # NB when recycling this script for extraction of other arguments from relclauses.
#                 # For object relclauses the list will have to be empty of potential objects!!!
#                 raise ValueError('Subject-relative clause must contain a relative pronoun subject!')
#
#         triples.append((node, 'nsubj', relcl_verb))
#         with open('C:\log_SILVIE.txt', 'a') as file:
#             file.write('haha')
#
#     return triples
#

"""Iveta -  en_verb_has_subject_is_relcl"""


def en_verb_has_subject_is_relcl(node):
     if node.upos != 'VERB':
         raise ValueError('It is not a verb.')
     if true_deprel(node) != 'acl:relcl':
         raise ValueError('It is not a relative clause.')
     ekids_controlleesAct_list = []
     ekids_controlleesPass_list = []
     ekids_controlleesPass_dobj_list = []
     ekids_controlleesPass_iobj_list = []
     ekids_01_list = echildren(node)
     if en_verb_controller_YN(node):
         for ekid_01 in ekids_01_list:
             # print(true_deprel(ekid_01), ekid_01.lemma)
             if true_deprel(ekid_01) == 'xcomp' and ekid_01.upos == 'VERB':
                 if not (en_verb_passive_form_YN(ekid_01)):
                     ekids_controlleesAct_list.append(ekid_01)
                 else:
                     ekids_controlleesPass_list.append(ekid_01)

         for ekid in ekids_controlleesPass_list:
             dobj_bool = False
             eskids = eschildren(ekid)
             for eskid in eskids:
                 if eskid.deprel in ('dobj', 'ccomp') or (eskid.deprel == 'xcomp' and not (eskid.lemma in ('call', 'consider'))):
                     dobj_bool = True
                     ekids_controlleesPass_iobj_list.append(ekid)
                     continue
             if not(dobj_bool):
                 ekids_controlleesPass_dobj_list.append(ekid)



     ekids_list = ekids_01_list
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
             for ekid_controllee in ekids_controlleesAct_list:
                 triples.append((ekid_controllee, 'nsubj', epar))
             for ekid_controllee in ekids_controlleesPass_dobj_list:
                 triples.append((ekid_controllee, 'dobj', epar))
             for ekid_controllee in ekids_controlleesPass_iobj_list:
                 triples.append((ekid_controllee, 'iobj', epar))
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
        if true_deprel(ekid) in ['dobj','ccomp'] or (true_deprel(ekid) == 'xcomp' and not (ekid.lemma in ('call', 'consider'))):
            # todo: funkce - seznam sloves, ktera maji xcomp jako doplnek adj nebo noun
            dobjs_list.append(ekid)
    if len(reldobjs_list) == 0:
        raise ValueError('Relative clause, but not obj, probably subject relclause.')
    if len(dobjs_list) !=0:
        raise ValueError('Is not direct object.')
    epar_list = eparents(node)
    triples = []
    for epar in epar_list:
        if epar.upos in ('NOUN', 'PROPN'):
            triples.append((node, 'dobj', epar))
            #    for ekid_controllee in ekids_controllees_list:
            #        triples.append((ekid_controllee, 'nsubj', epar))
    return triples





def en_verb_has_dobj_is_relclActive(node):  # does not check controlled werbs
    if node.upos != 'VERB':
        raise ValueError('It is not a verb.')
    if true_deprel(node) != 'acl:relcl':
        raise ValueError('It is not a relative clause.')
    active=False
    ekids_list = echildren(node)
    for ekid in ekids_list:
        if true_deprel(ekid) == 'nsubj':
            active=True
        if true_deprel(ekid) == 'nsubj' and ekid.feats['PronType'] == 'Rel':
            raise ValueError('It is a subject clause.')
        if (true_deprel(ekid) == 'dobj' and not(ekid.feats['PronType'] == 'Rel')):
            raise ValueError('Is not direct object.')
    if not active:
        raise ValueError('Verb is not active')
    epar_list = eparents(node)
    triples = []
    if not (en_verb_controller_YN(node)):
        for epar in epar_list:
            if epar.upos in ('NOUN', 'PROPN'):
                triples.append((node, 'dobj', epar))

    else:
         descends_list = node.descendants
         real_controllees = []
         for descend in descends_list:
             controlee_bool=False
             if descend.deprel == 'xcomp' and descend.upos == 'VERB':
                desc_kids = echildren(descend)
                for desc_kid in desc_kids:
                    if desc_kid.deprel == 'xcomp' and desc_kid.upos=='VERB':
                       controllee_bool=True
                if not(controlee_bool):
                    real_controllees.append(descend)

         for epar in epar_list:
             if epar.upos in ('NOUN', 'PROPN'):
                for real_controllee in real_controllees:
                    triples.append((real_controllee, 'dobj', epar))
    return triples

"""beginning of derivation functions"""

def en_verbs_001a_der_ADJx_N1__V1_ADVx(node,dictionary_param_1,dictionary_param_2,der_halucinate_param):
    triples = []
    verbs = der.get_verb_from_noun(node.lemma,dictionary_param_1)
    if len(verbs) == 0:
        eval.evaluate_neg(node, 'en_verbs_001a_der_ADJx_N1__V1_ADVx',None, "Does not exist verb derived from noun.")
    noun_childs = eschildren(node)
    noun_parents = eparents(node)
    try:
        adjs1 = noun_childs
    except:
        adjs1 = []
    try:
        adjs = adjs1 + noun_parents
    except:
        adjs = adjs1

    if len(adjs) == 0:
        eval.evaluate_neg(node, 'en_verbs_001a_der_ADJx_N1__V1_ADVx',None, "Noun does not have parents nor childs.")

    for adj in adjs:
        if ((adj in noun_parents) and (adj.upos == 'ADJ') and (node.deprel in ['nsubj', 'acl:relcl'])) or ((adj in noun_childs) and (adj.upos == 'ADJ')):
       # if (child.upos == 'ADJ') and (child.deprel == 'amod'):
            advs = der.get_adv_from_adj(adj.lemma,dictionary_param_2)
            if len(advs) == 0:
                eval.evaluate_neg(node, 'en_verbs_001a_der_ADJx_N1__V1_ADVx', adj, "Does not exist adv derived from adj.")
            for adv in advs:
                new_child = Node()
                new_child.lemma = adv.lemma
                new_child.upos='ADV'
                for verb in verbs:
                    v = Node()
                    v.lemma = verb.lemma
                    v.upos= 'VERB'
                    if ('der' in der_halucinate_param):
                        triples.append((v, 'en_verbs_001a_der_ADJx_N1__V1_ADVx', new_child))
                        eval.evaluate_triple(node,'en_verbs_001a_der_ADJx_N1__V1_ADVx',v,
                                             'en_verbs_001a_der_ADJx_N1__V1_ADVx', new_child,
                                             verb.type_of_deriv, adv.type_of_deriv, node.upos,
                                             adj.upos, v.upos, new_child.upos)
                    if ('halucinate' in der_halucinate_param):
                        triples.append((v, 'advmod', new_child))
                        eval.evaluate_triple(node, 'en_verbs_001a_der_ADJx_N1__V1_ADVx', v,
                                             'advmod', new_child,
                                             verb.type_of_deriv, adv.type_of_deriv, node.upos, adj.upos,
                                            v.upos, new_child.upos)
        else:
            eval.evaluate_neg(node,'en_verbs_001a_der_ADJx_N1__V1_ADVx',adj,"Parent or child is not adj or wrong deprel.")
    return triples

def en_nouns_001b_der_V1_ADVx__ADJx_N1(node, dictionary_param1,dictionary_param2,der_halucinate_param):
    triples = []

    verb_childs = eschildren(node)
    if len(verb_childs) == 0:
        eval.evaluate_neg(node, 'en_nouns_001b_der_V1_ADVx__ADJx_N1',None,"Verb does not have childs.")

    nouns = der.get_noun_from_verb(node.lemma, dictionary_param1)
    if len(nouns) == 0:
        eval.evaluate_neg(node, 'en_nouns_001b_der_V1_ADVx__ADJx_N1',None,"Does not exist noun derived from verb.")

    for child in verb_childs:
        if (child.upos == 'ADV') and (child.deprel == 'advmod'):
            adjs = der.get_adj_from_adv(child.lemma, dictionary_param2)
            if len(adjs) == 0:
                eval.evaluate_neg(node, 'en_nouns_001b_der_V1_ADVx__ADJx_N1',child, "Does not exist adj derived from adv.")
            for adj in adjs:
                new_child=Node()
                new_child.lemma=adj.lemma
                new_child.upos='ADJ'
                for noun in nouns:
                    n = Node()
                    n.lemma = noun.lemma
                    n.upos='NOUN'
                    if ('der') in der_halucinate_param:
                        triples.append((n, 'en_nouns_001b_der_V1_ADVx__ADJx_N1', new_child))
                        eval.evaluate_triple(node, 'en_nouns_001b_der_V1_ADVx__ADJx_N1', n,
                                             'en_nouns_001b_der_V1_ADVx__ADJx_N1', new_child,
                                             noun.type_of_deriv, adj.type_of_deriv, node.upos, child.upos,
                                             n.upos, new_child.upos)
                    if ('halucinate') in der_halucinate_param:
                        triples.append((n, 'amod', new_child))
                        eval.evaluate_triple(node, 'en_nouns_001b_der_V1_ADVx__ADJx_N1', n,
                                             'amod', new_child,
                                             noun.type_of_deriv, adj.type_of_deriv, node.upos, child.upos,
                                             n.upos, new_child.upos)
        else:
            eval.evaluate_neg(node, 'en_nouns_001b_der_V1_ADVx__ADJx_N1',child, "Child is not adverbium or its deprel is other than advmod." )
    return triples

def en_nouns_002a_der_V1_NX__Nx_N1(node,dictionary_param1,dictionary_param2,der_halucinate_param):
    triples = []
    parents=eparents(node)
    if len(parents) == 0:
        eval.evaluate_neg(node, 'en_nouns_002a_der_V1_NX__Nx_N1',None, "Noun does not have parents.")
    for parent in parents:
        if parent.upos == 'VERB' and node.deprel == 'dobj':
            nouns = der.get_noun_from_verb(parent.lemma, dictionary_param1)
            if len(nouns) == 0:
                eval.evaluate_neg(node, 'en_nouns_002a_der_V1_NX__Nx_N1', parent, "Does not exist noun derived from verb.")
            for noun in nouns:
                n = Node()
                n.lemma = noun.lemma
                n.upos='NOUN'
                if 'der' in der_halucinate_param:
                    triples.append((n, 'en_nouns_002a_der_V1_NX__Nx_N1', node))
                    eval.evaluate_triple(node, 'en_nouns_002a_der_V1_NX__Nx_N1', n,
                                     'en_nouns_002a_der_V1_NX__Nx_N1', node,
                                     noun.type_of_deriv, 'none', parent.upos, node.upos,
                                     n.upos, node.upos)
                if 'halucinate' in der_halucinate_param:
                    triples.append((n, 'compound' , node))
                    eval.evaluate_triple(node, 'en_nouns_002a_der_V1_NX__Nx_N1', n,
                                         'compound', node,
                                         noun.type_of_deriv, 'none', parent.upos, node.upos,
                                         n.upos, node.upos)
        else:
            eval.evaluate_neg(node, 'en_nouns_002a_der_V1_NX__Nx_N1',parent, "Noun parent is not verb or noun deprel is other than dobj.")
    return triples


def en_verbs_002b_der_Nx_N1__V1_Nx(node,dictionary_param1,dictionary_param2,der_halucinate_param):
    triples = []
    parents=eparents(node)
    if len(parents) == 0:
        eval.evaluate_neg(node, 'en_verbs_002b_der_Nx_N1__V1_Nx', None,"Noun does not have parent.")
    for parent in parents:
        if parent.upos == 'NOUN' and node.deprel == 'compound':
            verbs = der.get_verb_from_noun(parent.lemma,dictionary_param1)
            if len(verbs) == 0:
                eval.evaluate_neg(node, 'en_verbs_002b_der_Nx_N1__V1_Nx',parent,"Does not exist verb derived from noun.")
            for verb in verbs:
                v = Node()
                v.lemma = verb.lemma
                v.upos='VERB'
                if 'der' in der_halucinate_param:
                    triples.append((v, 'en_verbs_002b_der_Nx_N1__V1_Nx', node))
                    eval.evaluate_triple(node, 'en_verbs_002b_der_Nx_N1__V1_Nx', v,
                                         'en_verbs_002b_der_Nx_N1__V1_Nx', node,
                                         verb.type_of_deriv, 'none', node.upos, parent.upos,
                                         v.upos, node.upos)
                if 'halucinate' in der_halucinate_param:
                    triples.append((v, 'dep', node))
                    eval.evaluate_triple(node, 'en_verbs_002b_der_Nx_N1__V1_Nx', v,
                                         'dep', node,
                                         verb.type_of_deriv, 'none', node.upos, parent.upos,
                                         v.upos, node.upos)
        else:
            eval.evaluate_neg(node, 'en_verbs_002b_der_Nx_N1__V1_Nx',parent,"Noun parent is not noun or its deprel is other than compound.")
    return triples


def en_verbs_003a_der_ADJ1_Nx__V1_Nx(node, dictionary_param1, dictionary_param2, der_halucinate_param):
    triples = []
    nouns= []
    adj_parents = eparents(node)
    adj_childs = eschildren(node)
    try:
        nouns1 = adj_parents
    except:
        nouns1=[]
    try:
        nouns=nouns1 + adj_childs
    except:
        nouns = nouns1

    if len(nouns) == 0:
        eval.evaluate_neg(node, 'en_verbs_003a_der_ADJ1_Nx__V1_Nx',None,"Adj does not have parent nor childs.")

    for noun in nouns:
        #if noun.upos == 'NOUN':
        if ((noun in adj_childs) and (noun.upos == 'NOUN') and (noun.deprel in ['nsubj', 'acl:relcl'])) or ((noun in adj_parents) and (noun.upos == 'NOUN')):
            verbs = der.get_verb_from_adj(node.lemma,dictionary_param1)
            if len(verbs) == 0:
                eval.evaluate_neg(node, 'en_verbs_003a_der_ADJ1_Nx__V1_Nx', noun, "Does not exist derived verb from adj.")
            for verb in verbs:
                v = Node()
                v.lemma = verb.lemma
                v.upos='VERB'
                if 'der' in der_halucinate_param:
                    triples.append((verb, 'en_verbs_003a_der_ADJ1_Nx__V1_Nx', noun))
                    eval.evaluate_triple(node, 'en_verbs_003a_der_ADJ1_Nx__V1_Nx', v,
                                     'en_verbs_003a_der_ADJ1_Nx__V1_Nx', noun,
                                     verb.type_of_deriv, 'none', node.upos, noun.upos,
                                     v.upos, noun.upos)
                if 'halucinate' in der_halucinate_param:
                    triples.append((verb, 'dep', noun))
                    eval.evaluate_triple(node, 'en_verbs_003a_der_ADJ1_Nx__V1_Nx', v,
                                     'dep', noun,
                                     verb.type_of_deriv, 'none', node.upos, noun.upos,
                                     v.upos, noun.upos)
        if len(triples) == 0:
            eval.evaluate_neg(node, 'en_verbs_003a_der_ADJ1_Nx__V1_Nx',noun,"Parent or child is not noun or it has wrong deprel.")
    return triples


def en_nouns_003b_der_V1_Nx__ADJ1_Nx(node,dictionary_param1,dictionary_param2,der_halucinate_param):
    triples = []
    parents=eparents(node)
    if len(parents) == 0:
        eval.evaluate_neg(node, 'en_nouns_003b_der_V1_Nx__ADJ1_Nx',None, "Noun does not have parents.")
    for parent in parents:
        if ((parent.upos == 'VERB') and ((node.deprel == 'nsubj') or (node.deprel == 'dobj'))):
            adjs = der.get_adj_from_verb(parent.lemma,dictionary_param1)
            if len(adjs) == 0:
                eval.evaluate_neg(node, 'en_nouns_003b_der_V1_Nx__ADJ1_Nx',parent, "Adj derived from verb does not exist.")
            for adj in adjs:
                a = Node()
                a.lemma = adj.lemma
                a.upos='ADJ'
                #if (node.deprel == 'nsubj') or (node.deprel == 'dobj'):
                if 'der' in der_halucinate_param:
                    triples.append((a, 'en_nouns_003b_der_V1_Nx__ADJ1_Nx', node))
                    eval.evaluate_triple(node, 'en_nouns_003b_der_V1_Nx__ADJ1_Nx', a,
                                     'en_nouns_003b_der_V1_Nx__ADJ1_Nx', node,
                                     adj.type_of_deriv, 'none', parent.upos, node.upos,
                                     a.upos, node.upos)
                if 'halucinate' in der_halucinate_param:
                    triples.append((a, 'amod', node))
                    eval.evaluate_triple(node, 'en_nouns_003b_der_V1_Nx__ADJ1_Nx', a,
                                     'amod', node,
                                     adj.type_of_deriv, 'none', parent.upos, node.upos,
                                     a.upos, node.upos)
        else:
            eval.evaluate_neg(node, 'en_nouns_003b_der_V1_Nx__ADJ1_Nx',parent,"Parent is not verb.")
    return triples

def en_nouns_004a_der_V1_prepNX__N1_prepNx(node,dictionary_param1,dictionary_param2,der_halucinate_param):
    triples = []
    parents=eparents(node)
    if len(parents) == 0:
        eval.evaluate_neg(node, 'en_nouns_004a_der_V1_prepNX__N1_prepNx',None,"Noun does not have parent.")

    for parent in parents:
        if parent.upos == 'VERB' and node.deprel == 'nmod':
            nouns = der.get_noun_from_verb(parent.lemma,dictionary_param1)
            if len(nouns) == 0:
                eval.evaluate_neg(node, 'en_nouns_004a_der_V1_prepNX__N1_prepNx',parent,"Noun derived from verb does not exist.")
            for noun in nouns:
                n = Node()
                n.lemma = noun.lemma
                n.upos='NOUN'
                if 'der' in der_halucinate_param:
                    triples.append((n, 'en_nouns_004a_der_V1_prepNX__N1_prepNx', node))
                    eval.evaluate_triple(node, 'en_nouns_004a_der_V1_prepNX__N1_prepNx', n,
                                         'en_nouns_004a_der_V1_prepNX__N1_prepNx', node,
                                         noun.type_of_deriv, 'none', parent.upos, node.upos,
                                         n.upos, node.upos)
                if 'halucinate' in der_halucinate_param:
                    triples.append((n, 'nmod' , node))
                    eval.evaluate_triple(node, 'en_nouns_004a_der_V1_prepNX__N1_prepNx', n,
                                             'nmod', node,
                                             noun.type_of_deriv, 'none', parent.upos, node.upos,
                                             n.upos, node.upos)
        else:
            eval.evaluate_neg(node, 'en_nouns_004a_der_V1_prepNX__N1_prepNx', parent, "Parent is not verb or noun deprel is not nmod.")
    return triples

def en_verbs_004b_der_N1_prepNx__V1_prepNx(node,dictionary_param1,dictionnary_param2,der_halucinate_param):
    triples = []
    noun_parents = eparents(node)
    if len(noun_parents)==0:
        eval.evaluate_neg(node, 'en_verbs_004b_der_N1_prepNx__V1_prepNx',None, "Noun does not have parents.")
    for parent in noun_parents:
        if parent.upos == 'NOUN' and node.deprel == 'nmod':
            verbs = der.get_verb_from_noun(parent.lemma,dictionary_param1)
            if len(verbs)== 0:
                eval.evaluate_neg(node, 'en_verbs_004b_der_N1_prepNx__V1_prepNx',parent,"Verb derived from noun does not exist.")
            for verb in verbs:
                v= Node()
                v.lemma = verb.lemma
                v.upos='VERB'
                if 'der' in der_halucinate_param:
                    triples.append((v, 'en_verbs_004b_der_N1_prepNx__V1_prepNx', node))
                    eval.evaluate_triple(node, 'en_verbs_004b_der_N1_prepNx__V1_prepNx', v,
                                         'en_verbs_004b_der_N1_prepNx__V1_prepNx', node,
                                         verb.type_of_deriv, 'none', parent.upos, node.upos,
                                         v.upos, node.upos)
                if 'halucinate' in der_halucinate_param:
                    triples.append((v, 'nmod', node))
                    eval.evaluate_triple(node, 'en_verbs_004b_der_N1_prepNx__V1_prepNx', v,
                                         'nmod', node,
                                         verb.type_of_deriv, 'none', parent.upos, node.upos,
                                         v.upos, node.upos)
        else:
            eval.evaluate_neg(node, 'en_verbs_004b_der_N1_prepNx__V1_prepNx', parent, "Noun parent is not noun or it's deprel is not nmod.")
    return triples


def en_nouns_005_Nx_ADJ1__Nx_neg_ADJ1(node, dictionary_param1,dictionary_param2,der_halucinate_param):
    triples = []
    adjs = []
    noun_childs = eschildren(node)
    noun_parents = eparents(node)

    try:
        adjs1 = noun_parents
    except:
        adjs1=[]
    try:
        adjs=adjs1 + noun_childs
    except:
        adjs = adjs1

    if len(adjs) ==0:
        eval.evaluate_neg(node, 'en_nouns_005_Nx_ADJ1__Nx_neg_ADJ1', None, "Noun does not have childs nor parents.")

    for adj in adjs:
      if ((adj in noun_parents) and (adj.upos == 'ADJ') and (node.deprel in ['nsubj','acl:relcl'])) or ((adj in noun_childs) and (adj.upos == 'ADJ')):
            neg_adjs = der.get_neg_adj_from_adj(adj.lemma, dictionary_param1)
            if len(neg_adjs)==0:
                eval.evaluate_neg(node, 'en_nouns_005_Nx_ADJ1__Nx_neg_ADJ1', adj, "Neg_adj derived from adj does not exist.")
            for neg_adj in neg_adjs:
                new_neg_adj_node=Node()
                new_neg_adj_node.lemma=neg_adj.lemma
                new_neg_adj_node.upos='ADJ'
                if('der' in der_halucinate_param):
                    triples.append((node, 'en_nouns_005_Nx_ADJ1__Nx_neg_ADJ1',  new_neg_adj_node))
                    eval.evaluate_triple(node, 'en_nouns_005_Nx_ADJ1__Nx_neg_ADJ1', node,
                                         'en_nouns_005_Nx_ADJ1__Nx_neg_ADJ1',  new_neg_adj_node,
                                         neg_adj.type_of_deriv, 'none', node.upos , adj.upos,
                                         node.upos, new_neg_adj_node.upos)
                if ('halucinate' in der_halucinate_param):
                    triples.append((node, 'amod', new_neg_adj_node))
                    eval.evaluate_triple(node, 'en_nouns_005_Nx_ADJ1__Nx_neg_ADJ1', node,
                                         'amod', new_neg_adj_node,
                                         neg_adj.type_of_deriv, 'none', node.upos, adj.upos,
                                         node.upos, new_neg_adj_node.upos)
      else:
          eval.evaluate_neg(node, 'en_nouns_005_Nx_ADJ1__Nx_neg_ADJ1',adj, "Parent / child is not adj or wrong deprel.")

    return triples


"""beginning of real functions"""

def en_verbs_001a_V1_ADVx(node,dictionary_param_1,dictionary_param_2,der_halucinate_param):
    triples = []
    noun_childs = eschildren(node)

    for adv in noun_childs:
        if ((adv.deprel == 'advmod') and (adv.upos == 'ADV')):
            triples.append((node, 'advmod', adv))
            eval.evaluate_real(node, "en_verbs_001a_V1_ADVx", node, 'advmod', adv)
    return triples

def en_nouns_001b_003b_005_ADJx_N1(node, dictionary_param1,dictionary_param2,der_halucinate_param):
    triples = []
    noun_childs = eschildren(node)
    noun_parents = eparents(node)
    try:
        adjs1 = noun_childs
    except:
        adjs1 = []
    try:
        adjs = adjs1 + noun_parents
    except:
        adjs = adjs1

    for adj in adjs:
        if ((adj in noun_parents) and (adj.upos == 'ADJ') and (node.deprel in ['nsubj', 'acl:relcl'])) or ((adj in noun_childs) and (adj.upos == 'ADJ') and (adj.deprel == 'amod')):
            triples.append((node, 'amod', adj))
            eval.evaluate_real(node,"en_nouns_001b_003b_005_ADJx_N1", node, 'amod', adj)
    return triples

def en_nouns_002a_Nx_N1(node,dictionary_param1,dictionary_param2,der_halucinate_param):
    triples = []
    parents=eparents(node)
    for parent in parents:
        if parent.upos == 'NOUN' and node.deprel == 'compound':
            triples.append((parent, 'compound' , node))
            eval.evaluate_real(node, "en_nouns_002a_Nx_N1", node, 'compound', parent)

    return triples


def en_verbs_002b_003a_V1_Nx(node,dictionary_param1,dictionary_param2,der_halucinate_param):
    triples = []
    parents=eparents(node)
    for parent in parents:
       if parent.upos == 'VERB' and node.deprel == 'dep':
           triples.append((parent, 'dep', node))
           eval.evaluate_real(node, "en_verbs_002b_003a_V1_Nx", parent, 'dep', node)

    return triples




def en_nouns_004a_N1_prepNx(node,dictionary_param1,dictionary_param2,der_halucinate_param):
    triples = []
    parents=eparents(node)
    for parent in parents:
        if parent.upos == 'NOUN' and node.deprel == 'nmod':
            triples.append((parent, 'nmod' , node))
            eval.evaluate_real(node, 'en_nouns_004a_der_V1_prepNX__N1_prepNx', parent, 'nmod', node)

    return triples

def en_verbs_004b_V1_prepNx(node,dictionary_param1,dictionnary_param2,der_halucinate_param):
    triples = []
    noun_parents = eparents(node)
    for parent in noun_parents:
        if parent.upos == 'VERB' and node.deprel == 'nmod':
            triples.append((parent, 'nmod', node))
            eval.evaluate_real(node, 'en_verbs_004b_V1_prepNx', parent, 'nmod', node)
    return triples


