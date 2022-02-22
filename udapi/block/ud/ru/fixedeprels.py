"""Block to fix case-enhanced dependency relations in Russian."""
from udapi.core.block import Block
import logging
import re

class FixEdeprels(Block):

    # Secondary prepositions sometimes have the lemma of the original part of
    # speech. We want the grammaticalized form instead. List even those that
    # will have the same lexical form, as we also want to check the morphological
    # case. And include all other prepositions that have unambiguous morphological
    # case, even if they are not secondary.
    unambiguous = {
        'как':              'как' # remove morphological case
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
                for x in self.unambiguous:
                    # All secondary prepositions have only one fixed morphological case
                    # they appear with, so we can replace whatever case we encounter with the correct one.
                    m = re.match(r'^(obl(?::arg)?|nmod|advcl|acl(?::relcl)?):'+x+r'(?::(?:nom|gen|dat|acc|voc|loc|ins))?$', edep['deprel'])
                    if m:
                        edep['deprel'] = m.group(1)+':'+self.unambiguous[x]
                        solved = True
                        break
                # The following prepositions have more than one morphological case
                # available. Thanks to the Case feature on prepositions, we can
                # identify the correct one.
                if not solved:
                    m = re.match(r'^(obl(?::arg)?|nmod):(mezi|na|nad|o|po|pod|před|v|za)(?::(?:nom|gen|dat|voc))?$', edep['deprel'])
                    if m:
                        # The following is only partial solution. We will not see
                        # some children because they may be shared children of coordination.
                        prepchildren = [x for x in node.children if x.lemma == m.group(2)]
                        if len(prepchildren) > 0 and prepchildren[0].feats['Case'] != '':
                            edep['deprel'] = m.group(1)+':'+m.group(2)+':'+prepchildren[0].feats['Case'].lower()
                            solved = True
            if re.match(r'^(acl|advcl):', edep['deprel']):
                edep['deprel'] = re.sub(r'^(acl|advcl):(?:a|alespoň|až|jen|hlavně|například|ovšem_teprve|protože|teprve|totiž|zejména)_(aby|až|jestliže|když|li|pokud|protože|že)$', r'\1:\2', edep['deprel'])
                edep['deprel'] = re.sub(r'^(acl|advcl):i_(aby|až|jestliže|li|pokud)$', r'\1:\2', edep['deprel'])
                edep['deprel'] = re.sub(r'^(acl|advcl):(aby|až|jestliže|když|li|pokud|protože|že)_(?:ale|tedy|totiž|už|však)$', r'\1:\2', edep['deprel'])
            elif re.match(r'^(nmod|obl):', edep['deprel']):
                if edep['deprel'] == 'nmod:loc' and node.parent.feats['Case'] == 'Loc' or edep['deprel'] == 'nmod:voc' and node.parent.feats['Case'] == 'Voc':
                    # This is a same-case noun-noun modifier, which just happens to be in the locative.
                    # For example, 'v Ostravě-Porubě', 'Porubě' is attached to 'Ostravě', 'Ostravě' has
                    # nmod:v:loc, which is OK, but for 'Porubě' the case does not say anything significant.
                    edep['deprel'] = 'nmod'
                elif edep['deprel'] == 'nmod:loc':
                    edep['deprel'] = 'nmod:nom'
                elif edep['deprel'] == 'nmod:voc':
                    edep['deprel'] = 'nmod:nom'
                else:
                    # If one of the following expressions occurs followed by another preposition,
                    # remove the additional preposition. For example, 'i_když_s' becomes just 'i_když'.
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):ač([_:].+)?$', r'\1:ač', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):ačkoliv?([_:].+)?$', r'\1:ačkoli', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):byť[_:].+$', r'\1:byť', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):i_když[_:].+$', r'\1:i_když', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):jak[_:].+$', r'\1:jak', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):jakkoliv?[_:].+$', r'\1:jakkoli', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):jako[_:].+$', r'\1:jako', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):jakoby[_:].+$', r'\1:jako', edep['deprel']) # these instances in FicTree should be spelled 'jako by'

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
