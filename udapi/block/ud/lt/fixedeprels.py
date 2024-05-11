"""Block to fix case-enhanced dependency relations in Lithuanian."""
from udapi.core.block import Block
import logging
import re

class FixEdeprels(Block):

    # Sometimes there are multiple layers of case marking and only the outermost
    # layer should be reflected in the relation. For example, the semblative 'jako'
    # is used with the same case (preposition + morphology) as the nominal that
    # is being compared ('jako_v:loc' etc.) We do not want to multiply the relations
    # by all the inner cases.
    # The list in the value contains exceptions that should be left intact.
    outermost = {
        'kaip':    [],

        'než':     ['než_aby'],
        'třebaže': []
    }

    # Secondary prepositions sometimes have the lemma of the original part of
    # speech. We want the grammaticalized form instead. List even those that
    # will have the same lexical form, as we also want to check the morphological
    # case. And include all other prepositions that have unambiguous morphological
    # case, even if they are not secondary.
    unambiguous = {
        'apie':             'apie:acc', # about (topic)
        'dėl':              'dėl:gen', # because of
        'iki':              'iki:gen', # until
        'jei':              'jei', # remove morphological case # if
        'jeigu':            'jeigu', # remove morphological case # if
        'kaip':             'kaip', # remove morphological case # as, than
        'kaip_į':           'kaip',
        'kaip_per':         'kaip',
        'kaip_prieš':       'kaip',
        'kaip_su':          'kaip',
        'nes':              'nes', # remove morphological case # because
        'nors':             'nors', # remove morphological case # though, although, when, if
        'pagal':            'pagal:acc', # according to, under, by
        'pagal_dėl':        'pagal:acc',
        'per':              'per:acc', # through, over (přes)
        'prie':             'prie:gen', # to, at, near, under
        'tarp':             'tarp:gen', # between

        'aby_na':           'na:loc',
        'bez':              'bez:gen',
        'bez_ohled_na':     'bez_ohledu_na:acc',
        'bez_zřetel_k':     'bez_zřetele_k:dat',
        'bez_zřetel_na':    'bez_zřetele_na:acc',
        'že_za':            'za:gen'
    }

    def copy_case_from_adposition(self, node, adposition):
        """
        In some treebanks, adpositions have the Case feature and it denotes the
        valency case that the preposition's nominal must be in.
        """
        # The following is only partial solution. We will not see
        # some children because they may be shared children of coordination.
        prepchildren = [x for x in node.children if x.lemma == adposition]
        if len(prepchildren) > 0 and prepchildren[0].feats['Case'] != '':
            return adposition+':'+prepchildren[0].feats['Case'].lower()
        else:
            return None

    def process_node(self, node):
        """
        Occasionally the edeprels automatically derived from the Czech basic
        trees do not match the whitelist. For example, the noun is an
        abbreviation and its morphological case is unknown.
        """
        for edep in node.deps:
            m = re.match(r'^(obl(?::arg)?|nmod|advcl|acl(?::relcl)?):', edep['deprel'])
            if m:
                bdeprel = m.group(1)
                solved = False
                # Issues caused by errors in the original annotation must be fixed early.
                # Especially if acl|advcl occurs with a preposition that unambiguously
                # receives a morphological case in the subsequent steps, and then gets
                # flagged as solved.
                edep['deprel'] = re.sub(r'^advcl:do(?::gen)?$', r'obl:do:gen', edep['deprel']) # od nevidím do nevidím ###!!! Ale měli bychom opravit i závislost v základním stromu!
                edep['deprel'] = re.sub(r'^acl:k(?::dat)?$', r'acl', edep['deprel'])
                # If one of the following expressions occurs followed by another preposition
                # or by morphological case, remove the additional case marking. For example,
                # 'jako_v' becomes just 'jako'.
                for x in self.outermost:
                    exceptions = self.outermost[x]
                    m = re.match(r'^(obl(?::arg)?|nmod|advcl|acl(?::relcl)?):'+x+r'([_:].+)?$', edep['deprel'])
                    if m and m.group(2) and not x+m.group(2) in exceptions:
                        edep['deprel'] = m.group(1)+':'+x
                        solved = True
                        break
                if solved:
                    continue
                for x in self.unambiguous:
                    # All secondary prepositions have only one fixed morphological case
                    # they appear with, so we can replace whatever case we encounter with the correct one.
                    m = re.match(r'^(obl(?::arg)?|nmod|advcl|acl(?::relcl)?):'+x+r'(?::(?:nom|gen|dat|acc|voc|loc|ins))?$', edep['deprel'])
                    if m:
                        edep['deprel'] = m.group(1)+':'+self.unambiguous[x]
                        solved = True
                        break
                if solved:
                    continue
                # The following prepositions have more than one morphological case
                # available. Thanks to the Case feature on prepositions, we can
                # identify the correct one.
                m = re.match(r'^(obl(?::arg)?|nmod):(už)(?::(?:nom|gen|dat|voc))?$', edep['deprel'])
                if m:
                    adpcase = self.copy_case_from_adposition(node, m.group(2))
                    if adpcase and not re.search(r':(nom|gen|dat|voc)$', adpcase):
                        edep['deprel'] = m.group(1)+':'+adpcase
                        continue
            if re.match(r'^(acl|advcl):', edep['deprel']):
                # We do not include 'i' in the list of redundant prefixes because we want to preserve 'i když' (but we want to discard the other combinations).
                edep['deprel'] = re.sub(r'^(acl|advcl):(?:a|alespoň|až|jen|hlavně|například|ovšem_teprve|protože|teprve|totiž|zejména)_(aby|až|jestliže|když|li|pokud|protože|že)$', r'\1:\2', edep['deprel'])
                edep['deprel'] = re.sub(r'^(acl|advcl):i_(aby|až|jestliže|li|pokud)$', r'\1:\2', edep['deprel'])
                edep['deprel'] = re.sub(r'^(acl|advcl):(aby|až|jestliže|když|li|pokud|protože|že)_(?:ale|tedy|totiž|už|však)$', r'\1:\2', edep['deprel'])
            elif re.match(r'^(nmod|obl(:arg)?):', edep['deprel']):
                edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):ať:.+$', r'\1:ať', edep['deprel'])
                edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):beyond([_:].+)?$', r'\1', edep['deprel']) # Beyond the Limits

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
