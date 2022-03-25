"""Block to fix case-enhanced dependency relations in Russian."""
from udapi.core.block import Block
import logging
import re

class FixEdeprels(Block):

    # Sometimes there are multiple layers of case marking and only the outermost
    # layer should be reflected in the relation. For example, the semblative 'как'
    # is used with the same case (preposition + morphology) as the nominal that
    # is being compared ('как_в:loc' etc.) We do not want to multiply the relations
    # by all the inner cases.
    # The list in the value contains exceptions that should be left intact.
    outermost = {
        'будто':   [],
        'ведь':    [],
        'как':     ['как_только'],
        'словно':  [],
        'так_что': [],
        'чем':     []
    }

    # Secondary prepositions sometimes have the lemma of the original part of
    # speech. We want the grammaticalized form instead. List even those that
    # will have the same lexical form, as we also want to check the morphological
    # case. And include all other prepositions that have unambiguous morphological
    # case, even if they are not secondary.
    unambiguous = {
        'в_вид':            'в_виде:gen',
        'в_качество':       'в_качестве:gen',
        'в_отношение':      'в_отношении:gen',
        'в_связь_с':        'в_связи_с:ins',
        'в_течение':        'в_течение:gen',
        'в_ход':            'в_ходе:gen',
        'до':               'до:gen',
        'к':                'к:dat',
        'несмотря_на':      'несмотря_на:acc',
        'по_повод':         'по_поводу:gen',
        'помимо':           'помимо:gen',
        'при_помощь':       'при_помощи:gen',
        'с_помощь':         'с_помощью:gen',
        'со_сторона':       'со_стороны:gen',
        'согласно':         'согласно:dat',
        'спустя':           'спустя:acc'
    }

    def process_node(self, node):
        """
        Occasionally the edeprels automatically derived from the Russian basic
        trees do not match the whitelist. For example, the noun is an
        abbreviation and its morphological case is unknown.
        """
        for edep in node.deps:
            m = re.match(r'^(obl(?::arg)?|nmod|advcl|acl(?::relcl)?):', edep['deprel'])
            if m:
                bdeprel = m.group(1)
                solved = False
                # If one of the following expressions occurs followed by another preposition
                # or by morphological case, remove the additional case marking. For example,
                # 'словно_у' becomes just 'словно'.
                for x in self.outermost:
                    exceptions = self.outermost[x]
                    m = re.match(r'^(obl(?::arg)?|nmod|advcl|acl(?::relcl)?):'+x+r'([_:].+)?$', edep['deprel'])
                    if m and m.group(2) and not x+m.group(2) in exceptions:
                        edep['deprel'] = m.group(1)+':'+x
                        solved = True
                        break
                if solved:
                    break
                for x in self.unambiguous:
                    # All secondary prepositions have only one fixed morphological case
                    # they appear with, so we can replace whatever case we encounter with the correct one.
                    m = re.match(r'^(obl(?::arg)?|nmod|advcl|acl(?::relcl)?):'+x+r'(?::(?:nom|gen|dat|acc|voc|loc|ins))?$', edep['deprel'])
                    if m:
                        edep['deprel'] = m.group(1)+':'+self.unambiguous[x]
                        solved = True
                        break
                if solved:
                    break
                # The following prepositions have more than one morphological case
                # available. Thanks to the Case feature on prepositions, we can
                # identify the correct one.
                # Both "на" and "в" also occur with genitive. However, this
                # is only because there are numerals in the phrase ("в 9 случаев из 10")
                # and the whole phrase should not be analyzed as genitive.
                m = re.match(r'^(obl(?::arg)?|nmod):(в|на)(?::(?:nom|gen|dat|voc))?$', edep['deprel'])
                if m:
                    # The following is only partial solution. We will not see
                    # some children because they may be shared children of coordination.
                    prepchildren = [x for x in node.children if x.lemma == m.group(2)]
                    if len(prepchildren) > 0 and prepchildren[0].feats['Case'] != '':
                        edep['deprel'] = m.group(1)+':'+m.group(2)+':'+prepchildren[0].feats['Case'].lower()
                        solved = True
                    else:
                        # Accusative or locative are possible. Pick locative.
                        edep['deprel'] = m.group(1)+':'+m.group(2)+':loc'
                # Both "за" and "" also occur with instrumental. However, this
                # is only because there are numerals in the phrase ("за последние 20 лет")
                # and the whole phrase should be usually analyzed as accusative.
                m = re.match(r'^(obl(?::arg)?|nmod):(за)(?::(?:nom|gen|dat|voc|loc))?$', edep['deprel'])
                if m:
                    # The following is only partial solution. We will not see
                    # some children because they may be shared children of coordination.
                    prepchildren = [x for x in node.children if x.lemma == m.group(2)]
                    if len(prepchildren) > 0 and prepchildren[0].feats['Case'] != '':
                        edep['deprel'] = m.group(1)+':'+m.group(2)+':'+prepchildren[0].feats['Case'].lower()
                        solved = True
                    else:
                        # Accusative or instrumental are possible. Pick accusative.
                        edep['deprel'] = m.group(1)+':'+m.group(2)+':acc'
            if re.match(r'^(nmod|obl):', edep['deprel']):
                if edep['deprel'] == 'nmod:loc' and node.parent.feats['Case'] == 'Loc' or edep['deprel'] == 'nmod:voc' and node.parent.feats['Case'] == 'Voc':
                    # This is a same-case noun-noun modifier, which just happens to be in the locative.
                    # For example, 'v Ostravě-Porubě', 'Porubě' is attached to 'Ostravě', 'Ostravě' has
                    # nmod:v:loc, which is OK, but for 'Porubě' the case does not say anything significant.
                    edep['deprel'] = 'nmod'
                elif edep['deprel'] == 'nmod:loc':
                    edep['deprel'] = 'nmod:nom'
                elif edep['deprel'] == 'nmod:voc':
                    edep['deprel'] = 'nmod:nom'

    def set_basic_and_enhanced(self, node, parent, deprel, edeprel):
        '''
        Modifies the incoming relation of a node both in the basic tree and in
        the enhanced graph. If the node does not yet depend in the enhanced
        graph on the current basic parent, the new relation will be added without
        removing any old one. If the node already depends multiple times on the
        current basic parent in the enhanced graph, all such enhanced relations
        will be removed before adding the new one.
        '''
        old_parent = node.parent
        node.parent = parent
        node.deprel = deprel
        node.deps = [x for x in node.deps if x['parent'] != old_parent]
        new_edep = {}
        new_edep['parent'] = parent
        new_edep['deprel'] = edeprel
        node.deps.append(new_edep)
