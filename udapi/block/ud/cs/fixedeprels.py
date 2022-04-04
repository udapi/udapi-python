"""Block to fix case-enhanced dependency relations in Czech."""
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
        'abi':              'aby',
        'aby_na':           'na:loc',
        'ačkoliv':          'ačkoli',
        'ať':               'ať', # remove morphological case
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
        'po_v':             'po:loc',
        'po_doba':          'po_dobu:gen',
        'po_vzor':          'po_vzoru:gen',
        'poblíž':           'poblíž:gen',
        'počátek':          'počátkem:gen',
        'počínat':          'počínaje:ins',
        'pod_dojem':        'pod_dojmem:gen',
        'pod_vliv':         'pod_vlivem:gen',
        'podle':            'podle:gen',
        'pomoc':            'pomocí:gen',
        'pomocí':           'pomocí:gen',
        'postup':           'postupem:gen',
        'pouze_v':          'v:loc',
        'pro':              'pro:acc',
        'prostřednictví':   'prostřednictvím:gen',
        'prostřednictvím':  'prostřednictvím:gen',
        'proti':            'proti:dat',
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
        'směr_do':          'směrem_do:gen',
        'směr_k':           'směrem_k:dat',
        'směr_na':          'směrem_na:acc',
        'směr_od':          'směrem_od:gen',
        'společně_s':       'společně_s:ins',
        'spolu':            'spolu_s:ins',
        'spolu_s':          'spolu_s:ins',
        'stranou':          'stranou:gen',
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
        'z_důvod':          'z_důvodu:gen',
        'z_hledisko':       'z_hlediska:gen',
        'z_oblast':         'z_oblasti:gen',
        'z_řada':           'z_řad:gen',
        'z_strana':         'ze_strany:gen',
        'z_nedostatek':     'z_nedostatku:gen',
        'z_titul':          'z_titulu:gen',
        'za_pomoc':         'za_pomoci:gen',
        'za_účast':         'za_účasti:gen',
        'za_účel':          'za_účelem:gen',
        'začátek':          'začátkem:gen',
        'zásluha':          'zásluhou:gen',
        'zatím_co':         'zatímco',
        'závěr':            'závěrem:gen',
        'závisle_na':       'nezávisle_na:loc',
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
                edep['deprel'] = re.sub(r'^advcl:k(?::dat)?$', r'obl:k:dat', edep['deprel']) ###!!! Ale měli bychom opravit i závislost v základním stromu!
                edep['deprel'] = re.sub(r'^advcl:místo(?::gen)?$', r'obl:místo:gen', edep['deprel']) # 'v poslední době se množí bysem místo bych'
                edep['deprel'] = re.sub(r'^acl:na_způsob(?::gen)?$', r'nmod:na_způsob:gen', edep['deprel']) # 'střídmost na způsob Masarykova "jez dopolosyta"'
                edep['deprel'] = re.sub(r'^acl:od(?::gen)?$', r'nmod:od:gen', edep['deprel'])
                edep['deprel'] = re.sub(r'^advcl:od(?::gen)?$', r'obl:od:gen', edep['deprel']) # od nevidím do nevidím ###!!! Ale měli bychom opravit i závislost v základním stromu!
                edep['deprel'] = re.sub(r'^advcl:podle(?::gen)?$', r'obl:podle:gen', edep['deprel'])
                edep['deprel'] = re.sub(r'^advcl:pro(?::acc)?$', r'obl:pro:acc', edep['deprel'])
                edep['deprel'] = re.sub(r'^acl:v$', r'nmod:v:loc', edep['deprel'])
                edep['deprel'] = re.sub(r'^advcl:v$', r'obl:v:loc', edep['deprel'])
                edep['deprel'] = re.sub(r'^advcl:v_duchu?(?::gen)?$', r'obl:v_duchu:gen', edep['deprel'])
                # Removing 'až' must be done early. The remainder may be 'počátek'
                # and we will want to convert it to 'počátkem:gen'.
                edep['deprel'] = re.sub(r'^(nmod|obl(?::arg)?):až_(.+):(gen|dat|acc|loc|ins)', r'\1:\2:\3', edep['deprel'])
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
                if edep['deprel'] == 'nmod:loc' and node.parent.feats['Case'] == 'Loc' or edep['deprel'] == 'nmod:voc' and node.parent.feats['Case'] == 'Voc':
                    # This is a same-case noun-noun modifier, which just happens to be in the locative.
                    # For example, 'v Ostravě-Porubě', 'Porubě' is attached to 'Ostravě', 'Ostravě' has
                    # nmod:v:loc, which is OK, but for 'Porubě' the case does not say anything significant.
                    edep['deprel'] = 'nmod'
                elif edep['deprel'] == 'obl:loc':
                    # Annotation error. The first occurrence in PDT dev:
                    # 'V Rapaportu, ceníku Antverpské burzy i Diamantberichtu jsou uvedeny ceny...'
                    # The preposition 'V' should modify coordination 'Rapaportu i Diamantberichtu'.
                    # However, 'Rapaportu' is attached as 'obl' to 'Diamantberichtu'.
                    edep['deprel'] = 'obl:v:loc'
                elif edep['deprel'] == 'obl:arg:loc':
                    # Annotation error. The first occurrence in PDT dev:
                    edep['deprel'] = 'obl:arg:na:loc'
                elif edep['deprel'] == 'nmod:loc':
                    # 'působil v kanadském Edmontonu Oilers', 'Edmontonu' attached to 'Oilers' and not vice versa.
                    edep['deprel'] = 'nmod:nom'
                elif edep['deprel'] == 'obl:nom' or edep['deprel'] == 'obl:voc':
                    # Possibly an annotation error, nominative should be accusative, and the nominal should be direct object?
                    # However, there seems to be a great variability in the causes, some are subjects and many are really obliques, so let's go just with 'obl' for now.
                    edep['deprel'] = 'obl'
                elif edep['deprel'] == 'nmod:voc':
                    # 'v 8. čísle tiskoviny Ty rudá krávo'
                    edep['deprel'] = 'nmod:nom'
                elif edep['deprel'] == 'nmod:co:nom':
                    # Annotation error: 'kompatibilní znamená tolik co slučitelný'
                    # 'co' should be relative pronoun rather than subordinating conjunction.
                    edep['deprel'] = 'acl:relcl'
                    node.deprel = 'acl:relcl'
                elif re.match(r'^(obl(:arg)?):li$', edep['deprel']):
                    edep['deprel'] = 'advcl:li'
                elif re.match(r'^(nmod|obl(:arg)?):mezi:voc$', edep['deprel']):
                    edep['deprel'] = re.sub(r':voc$', r':acc', edep['deprel'])
                elif re.match(r'^(nmod|obl(:arg)?):mezi$', edep['deprel']):
                    if len([x for x in node.children if x.deprel == 'nummod:gov']) > 0:
                        edep['deprel'] += ':acc'
                    else:
                        edep['deprel'] += ':ins'
                elif re.match(r'^(nmod|obl(:arg)?):mimo$', edep['deprel']):
                    edep['deprel'] += ':acc'
                elif re.match(r'^(nmod|obl(:arg)?):místo$', edep['deprel']):
                    edep['deprel'] += ':gen'
                elif re.match(r'^obl:místo_za:acc$', edep['deprel']):
                    # 'chytají krávu místo za rohy spíše za ocas'
                    # This should be treated as coordination; 'místo' and 'spíše' are adverbs (???); 'case' for 'místo' does not seem to be the optimal solution.
                    for c in node.children:
                        if c.form == 'místo':
                            c.upos = 'ADV'
                            c.deprel = 'cc'
                    edep['deprel'] = 'obl:za:acc'
                elif re.match(r'^(nmod|obl(:arg)?):místo[_:].+$', edep['deprel']) and not re.match(r'^(nmod|obl(:arg)?):místo_aby$', edep['deprel']):
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):místo[_:].+$', r'\1:místo:gen', edep['deprel'])
                elif re.match(r'^(nmod|obl(:arg)?):na(:gen)?$', edep['deprel']):
                    edep['deprel'] = re.sub(r':gen$', '', edep['deprel'])
                    # The case is unknown. We need 'acc' or 'loc'.
                    # The locative is probably more frequent but it is not so likely with every noun.
                    # If there is an nummod:gov child, it must be accusative and not locative.
                    # (The case would be taken from the number but if it is expressed as digits, it does not have the case feature.)
                    if len([x for x in node.children if x.deprel == 'nummod:gov']) > 0:
                        edep['deprel'] += ':acc'
                    elif re.match(r'^(adresát|AIDS|DEM|frank|h|ha|hodina|Honolulu|jméno|koruna|litr|metr|míle|miliarda|milión|mm|MUDr|NATO|obyvatel|OSN|počet|procento|příklad|rok|SSSR|vůz)$', node.lemma):
                        edep['deprel'] += ':acc'
                    else:
                        edep['deprel'] += ':loc'
                elif re.match(r'^obl:arg:na_konec$', edep['deprel']):
                    # Annotation error. It should have been two prepositional phrases: 'snížil na 225 tisíc koncem minulého roku'
                    edep['deprel'] = 'obl:arg:na:acc'
                elif re.match(r'^(nmod|obl(:arg)?):nad$', edep['deprel']):
                    if re.match(r'[0-9]', node.lemma) or len([x for x in node.children if x.deprel == 'nummod:gov']) > 0:
                        edep['deprel'] += ':acc'
                    else:
                        edep['deprel'] += ':ins'
                elif re.match(r'^(nmod|obl(:arg)?):o$', edep['deprel']):
                    if re.match(r'[0-9]', node.lemma) or len([x for x in node.children if x.deprel == 'nummod:gov']) > 0:
                        edep['deprel'] += ':acc'
                    else:
                        edep['deprel'] += ':loc'
                elif re.match(r'^(nmod|obl(:arg)?):ohled_na:ins$', edep['deprel']):
                    # Annotation error.
                    if node.form == 's':
                        ohled = node.next_node
                        na = ohled.next_node
                        noun = na.next_node
                        self.set_basic_and_enhanced(noun, node.parent, 'obl', 'obl:s_ohledem_na:acc')
                        self.set_basic_and_enhanced(ohled, node, 'fixed', 'fixed')
                        self.set_basic_and_enhanced(na, node, 'fixed', 'fixed')
                        self.set_basic_and_enhanced(node, noun, 'case', 'case')
                elif re.match(r'^nmod:pára:nom$', edep['deprel']):
                    # Annotation error: 'par excellence'.
                    edep['deprel'] = 'nmod'
                    for c in node.children:
                        if c.udeprel == 'case' and c.form.lower() == 'par':
                            c.lemma = 'par'
                            c.upos = 'ADP'
                            c.xpos = 'RR--X----------'
                            c.feats['Case'] = ''
                            c.feats['Gender'] = ''
                            c.feats['Number'] = ''
                            c.feats['Polarity'] = ''
                            c.feats['AdpType'] = 'Prep'
                elif re.match(r'^(nmod|obl(:arg)?):po$', edep['deprel']):
                    if len([x for x in node.children if x.deprel == 'nummod:gov']) > 0:
                        edep['deprel'] += ':acc'
                    else:
                        edep['deprel'] += ':loc'
                elif re.match(r'^(nmod|obl(:arg)?):pod$', edep['deprel']):
                    if re.match(r'[0-9]', node.lemma) or len([x for x in node.children if x.deprel == 'nummod:gov']) > 0:
                        edep['deprel'] += ':acc'
                    else:
                        edep['deprel'] += ':ins'
                elif re.match(r'^(nmod|obl(:arg)?):před$', edep['deprel']):
                    # Accusative would be possible but unlikely.
                    edep['deprel'] += ':ins'
                elif re.match(r'^(nmod|obl(:arg)?):s$', edep['deprel']):
                    # Genitive would be possible but unlikely.
                    edep['deprel'] += ':ins'
                elif re.match(r'^(nmod|obl(:arg)?):v_s(:loc)?$', edep['deprel']) and node.form == 'spolupráci':
                    # Annotation error. 'Ve spolupráci s' should be analyzed as a multi-word preposition.
                    # Find the content nominal.
                    cnouns = [x for x in node.children if x.ord > node.ord and re.match(r'^(nmod|obl)', x.udeprel)]
                    vs = [x for x in node.children if x.ord < node.ord and x.lemma == 'v']
                    if len(cnouns) > 0 and len(vs) > 0:
                        cnoun = cnouns[0]
                        v = vs[0]
                        self.set_basic_and_enhanced(cnoun, node.parent, 'obl', 'obl:ve_spolupráci_s:ins')
                        self.set_basic_and_enhanced(v, cnoun, 'case', 'case')
                        self.set_basic_and_enhanced(node, v, 'fixed', 'fixed')
                elif re.match(r'^(nmod|obl(:arg)?):v(:nom)?$', edep['deprel']):
                    # ':nom' occurs in 'karneval v Rio de Janeiro'
                    edep['deprel'] = re.sub(r':nom$', '', edep['deprel'])
                    if len([x for x in node.children if x.deprel == 'nummod:gov']) > 0:
                        edep['deprel'] += ':acc'
                    else:
                        edep['deprel'] += ':loc'
                elif re.match(r'^obl:v_čel[eo]_s:ins$', edep['deprel']):
                    # There is just one occurrence and it is an error:
                    # 'Předloňský kůň roku Law Soziri šel již v Lahovickém oblouku v čele s Raddelliosem a tato dvojice také nakonec zahanbila ostatní soupeře...'
                    # There should be two independent oblique modifiers, 'v čele' and 's Raddelliosem'.
                    edep['deprel'] = 'obl:s:ins'
                elif re.match(r'^(nmod|obl(:arg)?):za$', edep['deprel']):
                    # Instrumental would be possible but unlikely.
                    edep['deprel'] += ':acc'
                else:
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):a([_:].+)?$', r'\1', edep['deprel']) # ala vršovický dloubák
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):a_?l[ae]([_:].+)?$', r'\1', edep['deprel']) # a la bondovky
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):(jak_)?ad([_:].+)?$', r'\1', edep['deprel']) # ad infinitum
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):ať:.+$', r'\1:ať', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):beyond([_:].+)?$', r'\1', edep['deprel']) # Beyond the Limits
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):co(:nom)?$', r'advmod', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):de([_:].+)?$', r'\1', edep['deprel']) # de facto
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):di([_:].+)?$', r'\1', edep['deprel']) # Lido di Jesolo
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):en([_:].+)?$', r'\1', edep['deprel']) # bienvenue en France
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):in([_:].+)?$', r'\1', edep['deprel']) # made in NHL
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):into([_:].+)?$', r'\1', edep['deprel']) # made in NHL
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):jméno:nom$', r'\1:jménem:nom', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):jméno(:gen)?$', r'\1:jménem:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):mezi:(nom|dat)$', r'\1:mezi:ins', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):o:(nom|gen|dat)$', r'\1:o:acc', edep['deprel']) # 'zájem o obaly'
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):of([_:].+)?$', r'\1', edep['deprel']) # University of North Carolina
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):per([_:].+)?$', r'\1', edep['deprel']) # per rollam
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):po:(nom|gen)$', r'\1:po:acc', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):před:gen$', r'\1:před:ins', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):přestože[_:].+$', r'\1:přestože', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):se?:(nom|acc|ins)$', r'\1:s:ins', edep['deprel']) # accusative: 'být s to' should be a fixed expression and it should be the predicate!
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):shoda(:gen)?$', r'\1', edep['deprel']) # 'shodou okolností' is not a prepositional phrase
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):v:gen$', r'\1:v:loc', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):vo:acc$', r'\1:o:acc', edep['deprel']) # colloquial: vo všecko
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):von([_:].+)?$', r'\1', edep['deprel']) # von Neumannem
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):voor([_:].+)?$', r'\1', edep['deprel']) # Hoge Raad voor Diamant
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):z:nom$', r'\1:z:gen', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):z:ins$', r'\1:s:ins', edep['deprel'])
                    edep['deprel'] = re.sub(r'^(nmod|obl(:arg)?):za:nom$', r'\1:za:acc', edep['deprel'])
                    edep['deprel'] = re.sub(r'^nmod:že:gen$', 'acl:že', edep['deprel'])

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
