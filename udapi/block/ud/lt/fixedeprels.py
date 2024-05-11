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
        'ač':      [],
        'ačkoli':  [], # 'ačkoliv' se převede na 'ačkoli' dole
        'byť':     [],
        'i_když':  [],
        'jak':     [],
        'jakkoli': [], # 'jakkoliv' se převede na 'jakkoli' dole
        'jako':    [],
        'jakoby':  ['jakoby_pod:ins'], # these instances in FicTree should be spelled 'jako by'
        'než':     ['než_aby'],
        'protože': [],
        'takže':   [],
        'třebaže': []
    }

    # Secondary prepositions sometimes have the lemma of the original part of
    # speech. We want the grammaticalized form instead. List even those that
    # will have the same lexical form, as we also want to check the morphological
    # case. And include all other prepositions that have unambiguous morphological
    # case, even if they are not secondary.
    unambiguous = {
        'nes':              'nes', # remove morphological case # because

        'aby_na':           'na:loc',
        'ačkoliv':          'ačkoli',
        'ať_forma':         'formou:gen',
        'ať_v':             'v:loc',
        'ať_z':             'z:gen',
        'ať_z_strana':      'ze_strany:gen',
        'až_do':            'do:gen',
        'až_o':             'o:acc',
        'během':            'během:gen',
        'bez':              'bez:gen',
        'bez_ohled_na':     'bez_ohledu_na:acc',
        'bez_zřetel_k':     'bez_zřetele_k:dat',
        'bez_zřetel_na':    'bez_zřetele_na:acc',
        'blíž':             'blízko:dat',
        'cesta':            'cestou:gen',
        'daleko':           'nedaleko:gen',
        'daleko_od':        'od:gen',
        'dík':              'díky:dat',
        'díky':             'díky:dat',
        'dle':              'dle:gen',
        'do':               'do:gen',
        'do_k':             'k:dat',
        'do_oblast':        'do_oblasti:gen',
        'do_rozpor_s':      'do_rozporu_s:ins',
        'do_soulad_s':      'do_souladu_s:ins',
        'forma':            'formou:gen',
        'i_když':           'i_když', # remove morphological case
        'jak_aby':          'jak',
        'jak_ad':           'jak',
        'jakkoliv':         'jakkoli',
        'jako':             'jako', # remove morphological case
        'jako_kupříkladu':  'jako',
        'jakoby':           'jako',
        'jakoby_pod':       'pod:ins',
        'jelikož_do':       'jelikož',
        'jestli_že':        'jestliže',
        'k':                'k:dat',
        'k_konec':          'ke_konci:gen',
        'kdykoliv':         'kdykoli',
        'kol':              'kolem:gen',
        'kolem':            'kolem:gen',
        'konec':            'koncem:gen',
        'krom':             'kromě:gen',
        'kromě':            'kromě:gen',
        'liž':              'li',
        'mezi_uvnitř':      'uvnitř:gen',
        'na_báze':          'na_bázi:gen',
        'na_čelo':          'na_čele:gen',
        'na_mimo':          'na:loc', # na kurtě i mimo něj
        'na_než':           'na:acc', # na víc než čtyři a půl kilometru
        'na_od':            'na_rozdíl_od:gen',
        'na_podklad':       'na_podkladě:gen',
        'na_rozdíl_od':     'na_rozdíl_od:gen',
        'na_újma':          'gen', # 'nebude na újmu' is a multi-word predicate but 'na újmu' is probably not used as an independent oblique modifier
        'na_úroveň':        'na_úrovni:gen',
        'na_úsek':          'na_úseku:gen',
        'na_základ':        'na_základě:gen',
        'na_základna':      'na_základně:gen',
        'na_závěr':         'na_závěr:gen',
        'namísto':          'namísto:gen',
        'namísto_do':       'do:gen',
        'narozdíl_od':      'na_rozdíl_od:gen',
        'následek':         'následkem:gen',
        'navzdory':         'navzdory:dat',
        'nedaleko':         'nedaleko:gen',
        'než':              'než', # remove morphological case
        'nežli':            'nežli', # remove morphological case
        'o_jako':           'jako',
        'o_o':              'o:acc',
        'od':               'od:gen',
        'ohledně':          'ohledně:gen',
        'okolo':            'okolo:gen',
        'oproti':           'oproti:dat',
        'protože':          'protože', # remove morphological case
        'před_během':       'během:gen', # před a během utkání
        'před_po':          'po:loc', # před a po vyloučení Schindlera
        'přes':             'přes:acc',
        'přestože':         'přestože', # remove morphological case
        'při':              'při:loc',
        'při_příležitost':  'při_příležitosti:gen',
        's_ohled_k':        's_ohledem_k:dat',
        's_ohled_na':       's_ohledem_na:acc',
        's_pomoc':          's_pomocí:gen',
        's_přihlédnutí_k':  's_přihlédnutím_k:dat',
        's_přihlédnutí_na': 's_přihlédnutím_na:acc',
        's_výjimka':        's_výjimkou:gen',
        's_vyloučení':      's_vyloučením:gen',
        's_zřetel_k':       'se_zřetelem_k:dat',
        's_zřetel_na':      'se_zřetelem_na:acc',
        'severně_od':       'od:gen',
        'skrz':             'skrz:acc',
        'takže':            'takže', # remove morphological case
        'takže_a':          'takže',
        'třebaže':          'třebaže', # remove morphological case
        'u':                'u:gen',
        'u_příležitost':    'u_příležitosti:gen',
        'uprostřed':        'uprostřed:gen',
        'uvnitř':           'uvnitř:gen',
        'v_analogie_s':     'v_analogii_s:ins',
        'v_čelo':           'v_čele:gen',
        'v_čelo_s':         'v_čele_s:ins',
        'v_dohoda_s':       'v_dohodě_s:ins',
        'v_duch':           'v_duchu:gen',
        'v_důsledek':       'v_důsledku:gen',
        'v_forma':          've_formě:gen',
        'v_jméno':          've_jménu:gen',
        'v_k':              'k:dat',
        'v_kombinace_s':    'v_kombinaci_s:ins',
        'v_konfrontace_s':  'v_konfrontaci_s:ins',
        'v_kontext_s':      'v_kontextu_s:ins',
        'v_na':             'na:loc',
        'v_oblast':         'v_oblasti:gen',
        'v_oblast_s':       's:ins',
        'v_obor':           'v_oboru:gen',
        'v_otázka':         'v_otázce:gen',
        'v_podoba':         'v_podobě:gen',
        'v_poměr_k':        'v_poměru_k:dat',
        'v_proces':         'v_procesu:gen',
        'v_prospěch':       've_prospěch:gen',
        'v_protiklad_k':    'v_protikladu_k:dat',
        'v_průběh':         'v_průběhu:gen',
        'v_případ':         'v_případě:gen',
        'v_případ_že':      'v_případě_že',
        'v_rámec':          'v_rámci:gen',
        'v_rozpor_s':       'v_rozporu_s:ins',
        'v_řada':           'v_řadě:gen',
        'v_shoda_s':        've_shodě_s:ins',
        'v_služba':         've_službách:gen',
        'v_směr':           've_směru:gen',
        'v_směr_k':         've_směru_k:dat',
        'v_smysl':          've_smyslu:gen',
        'v_součinnost_s':   'v_součinnosti_s:ins',
        'v_souhlas_s':      'v_souhlasu_s:ins',
        'v_soulad_s':       'v_souladu_s:ins',
        'v_souvislost_s':   'v_souvislosti_s:ins',
        'v_spojení_s':      've_spojení_s:ins',
        'v_spojený_s':      've_spojení_s:ins',
        'v_spojitost_s':    've_spojitosti_s:ins',
        'v_spolupráce_s':   've_spolupráci_s:ins',
        'v_s_spolupráce':   've_spolupráci_s:ins',
        'v_srovnání_s':     've_srovnání_s:ins',
        'v_srovnání_se':    've_srovnání_s:ins',
        'v_světlo':         've_světle:gen',
        'v_věc':            've_věci:gen',
        'v_vztah_k':        've_vztahu_k:dat',
        'v_zájem':          'v_zájmu:gen',
        'v_záležitost':     'v_záležitosti:gen',
        'v_závěr':          'v_závěru:gen',
        'v_závislost_na':   'v_závislosti_na:loc',
        'v_závislost_s':    'v_závislosti_s:ins',
        'v_znamení':        've_znamení:gen',
        'včetně':           'včetně:gen',
        'vedle':            'vedle:gen',
        'vina':             'vinou:gen',
        'vliv':             'vlivem:gen',
        'vůči':             'vůči:dat',
        'vzhledem':         'vzhledem_k:dat',
        'vzhledem_k':       'vzhledem_k:dat',
        'z':                'z:gen',
        'že':               'že', # remove morphological case
        'že_ať':            'ať',
        'že_jako':          'že',
        'že_jakoby':        'že',
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
                m = re.match(r'^(obl(?::arg)?|nmod):(mezi|na|nad|o|po|pod|před|v|za)(?::(?:nom|gen|dat|voc))?$', edep['deprel'])
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
                edep['deprel'] = re.sub(r'^(acl|advcl):co_když$', r'\1', edep['deprel'])
                edep['deprel'] = re.sub(r'^(acl|advcl):kdy$', r'\1', edep['deprel'])
                edep['deprel'] = re.sub(r'^(advcl):neboť$', r'\1', edep['deprel']) # 'neboť' is coordinating
                edep['deprel'] = re.sub(r'^(advcl):nechť$', r'\1', edep['deprel'])
                if edep['deprel'] == 'acl:v' and node.form == 'patře':
                    edep['deprel'] = 'nmod:v:loc'
                    node.deprel = 'nmod'
                    node.lemma = 'patro'
                    node.upos = 'NOUN'
                    node.xpos = 'NNNS6-----A----'
                    node.feats['Aspect'] = ''
                    node.feats['Gender'] = 'Neut'
                    node.feats['Tense'] = ''
                    node.feats['VerbForm'] = ''
                    node.feats['Voice'] = ''
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
