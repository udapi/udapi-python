"""
This block searches for relative clauses modifying a determiner ('el que...').
It is written for Catalan but a similar block should work for Spanish and other
Romance languages.
"""
from udapi.core.block import Block
import logging
import re

class ElQue(Block):

    def __init__(self, fix=False, **kwargs):
        """
        Default: Print the annotation patterns but do not fix anything.
        fix=1: Do not print the patterns but fix them.
        """
        super().__init__(**kwargs)
        self.fix = fix

    def process_node(self, node):
        # We take 'que' as the central node of the construction.
        if node.lemma == 'que' and node.upos == 'PRON' and node.parent.ord > node.ord:
            # We will refer to the parent of 'que' as a verb, although it can be
            # a non-verbal predicate, too.
            que = node
            verb = node.parent
            # Check the lemma of the determiner. The form may vary for gender and number.
            if que.prev_node and que.prev_node.lemma == 'el':
                el = que.prev_node
                adp = None
                if el.prev_node and el.prev_node.upos == 'ADP':
                    adp = el.prev_node
                    if adp.udeprel == 'fixed':
                        adp = adp.parent
                if self.fix:
                    self.fix_pattern(adp, el, que, verb)
                else:
                    self.print_pattern(adp, el, que, verb)

    def print_pattern(self, adp, el, que, verb):
        stanford = []
        if adp:
            if adp.parent == el:
                parentstr = 'el'
            elif adp.parent == que:
                parentstr = 'que'
            elif adp.parent == verb:
                parentstr = 'VERB'
            else:
                parentstr = 'OTHER'
            stanford.append(adp.deprel + '(' + parentstr + ', ADP)')
        if el.parent == adp:
            parentstr = 'ADP'
        elif el.parent == que:
            parentstr = 'que'
        elif el.parent == verb:
            parentstr = 'VERB'
        else:
            parentstr = 'OTHER'
        stanford.append(el.deprel + '(' + parentstr + ', el)')
        # We found the verb as the parent of 'que', so we do not need to check the parent of 'que' now.
        stanford.append(que.deprel + '(VERB, que)')
        if verb.parent == adp:
            parentstr = 'ADP'
        elif verb.parent == el:
            parentstr = 'el'
        else:
            parentstr = 'OTHER'
        stanford.append(verb.deprel + '(' + parentstr + ', VERB)')
        print('; '.join(stanford))

    def fix_pattern(self, adp, el, que, verb):
        if adp:
            if adp.parent == que or adp.parent == verb:
                attach(adp, el, 'case')
        if el.parent == que:
            ###!!! Just a temporary change. In the end it will be attached elsewhere.
            attach(el, verb)
            el.parent = verb
            if len(el.deps) == 1:
                el.deps[0]['parent'] = verb
        if verb.parent != adp and verb.parent != el and verb.parent != que:
            eldeprel = None
            if re.match(r'^[nc]subj$', verb.udeprel):
                eldeprel = 'nsubj'
            elif re.match(r'^ccomp$', verb.udeprel):
                eldeprel = 'obj'
            elif re.match(r'^advcl$', verb.udeprel):
                eldeprel = 'obl'
            elif re.match(r'^acl$', verb.udeprel):
                eldeprel = 'nmod'
            elif re.match(r'^(xcomp|conj|appos|root)$', verb.udeprel):
                eldeprel = verb.deprel
            if eldeprel:
                attach(el, verb.parent, eldeprel)
                attach(verb, el, 'acl:relcl')
                # If anything before 'el' depends on the verb ('cc', 'mark', 'punct' etc.),
                # re-attach it to 'el'.
                for c in verb.children:
                    if c.ord < el.ord and re.match(r'^(cc|mark|case|punct)$', c.udeprel):
                        attach(c, el)

def attach(node, parent, deprel=None):
    """
    Attach a node to a new parent with a new deprel in the basic tree. In
    addition, if there are enhanced dependencies and there is just one incoming
    enhanced relation (this is the case in AnCora), this relation will be
    modified accordingly.
    """
    node.parent = parent
    if deprel:
        node.deprel = deprel
    if len(node.deps) == 1:
        node.deps[0]['parent'] = parent
        if deprel:
            node.deps[0]['deprel'] = deprel
