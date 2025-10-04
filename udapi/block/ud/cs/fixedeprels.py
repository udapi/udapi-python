"""Block to fix case-enhanced dependency relations in Czech."""
from udapi.core.block import Block
import re

class FixEdeprels(Block):

    # Sometimes there are multiple layers of case marking and only the outermost
    # layer should be reflected in the relation. For example, the semblative 'jako'
    # is used with the same case (preposition + morphology) as the nominal that
    # is being compared ('jako_v:loc' etc.) We do not want to multiply the relations
    # by all the inner cases.
    # The list in the value contains exceptions that should be left intact.
    outermost = {
        'aby':     [],
        'ač':      [],
        'ačkoli':  [], # 'ačkoliv' se převede na 'ačkoli' dole
        'ačkoliv': [], # ... ale možná ne když je doprovázeno předložkou
        'ať':      [],
        'byť':     [],
        'i_když':  [],
        'jak':     [],
        'jakkoli': [], # 'jakkoliv' se převede na 'jakkoli' dole
        'jako':    [],
        'jakoby':  ['jakoby_pod:ins'], # these instances in FicTree should be spelled 'jako by'
        'když':    [],
        'než':     ['než_aby'],
        'nežli':   [],
        'pokud':   [],
        'protože': [],
        'takže':   [],
        'třebaže': [],
        'že':      []
    }

    # Secondary prepositions sometimes have the lemma of the original part of
    # speech. We want the grammaticalized form instead. List even those that
    # will have the same lexical form, as we also want to check the morphological
    # case. And include all other prepositions that have unambiguous morphological
    # case, even if they are not secondary.
    unambiguous = {
        'á':                'na:acc', # "á konto té záležitosti", ovšem "á konto" není ani spojeno jako složená předložka (význam = "na konto")
        'abi':              'aby',
        'aby_na':           'na:loc',
        'ačkoliv':          'ačkoli',
        'ať':               'ať', # remove morphological case
        'ať_forma':         'formou:gen',
        'ať_jako':          'jako',
        'ať_na':            'na:loc',
        'ať_s':             's:ins',
        'ať_v':             'v:loc',
        'ať_v_oblast':      'v_oblasti:gen',
        'ať_z':             'z:gen',
        'ať_z_hledisko':    'z_hlediska:gen',
        'ať_z_strana':      'ze_strany:gen',
        'až_do':            'do:gen',
        'až_o':             'o:acc',
        'během':            'během:gen',
        'bez':              'bez:gen',
        'bez_ohled_na':     'bez_ohledu_na:acc',
        'bez_na':           'bez_ohledu_na:acc', ###!!! a temporary hack to silence the validator about (https://github.com/UniversalDependencies/UD_Czech-PDT/issues/10#issuecomment-2710721703)
        'bez_zřetel_k':     'bez_zřetele_k:dat',
        'bez_zřetel_na':    'bez_zřetele_na:acc',
        'blízko':           'blízko:dat',
        'blízko_k':         'blízko:dat',
        'blíž':             'blízko:dat',
        'blíže':            'blízko:dat',
        'bok_po_bok_s':     'bok_po_boku_s:ins',
        'cesta':            'cestou:gen',
        'co_jako':          'jako',
        'coby':             'coby', # remove morphological case
        'daleko':           'nedaleko:gen',
        'daleko_od':        'od:gen',
        'dík':              'díky:dat',
        'díky':             'díky:dat',
        'dle':              'dle:gen',
        'do':               'do:gen',
        'do_čelo':          'do_čela:gen',
        'do_k':             'k:dat',
        'do_oblast':        'do_oblasti:gen',
        'do_rozpor_s':      'do_rozporu_s:ins',
        'do_ruka':          'do_rukou:gen',
        'do_soulad_s':      'do_souladu_s:ins',
        'důsledkem':        'v_důsledku:gen',
        'forma':            'formou:gen',
        'formou':           'formou:gen',
        'hledět_na':        'nehledě_na:acc',
        'i_když':           'i_když', # remove morphological case
        'i_pro':            'pro:acc',
        'jak_aby':          'jak',
        'jak_ad':           'jak',
        'jakkoliv':         'jakkoli',
        'jako':             'jako', # remove morphological case
        'jako_kupříkladu':  'jako',
        'jakoby':           'jako',
        'jakoby_pod':       'pod:ins',
        'jakožto':          'jako',
        'jelikož_do':       'jelikož',
        'jenom':            'jen',
        'jesli':            'jestli',
        'jestli_že':        'jestliže',
        'jménem':           'jménem:gen',
        'k':                'k:dat',
        'k_konec':          'ke_konci:gen',
        'k_prospěch':       'ku_prospěchu:gen',
        'kdykoliv':         'kdykoli',
        'kol':              'kolem:gen',
        'kolem':            'kolem:gen',
        'kolem_dokola':     'kolem:gen',
        'koncem':           'koncem:gen',
        'konec':            'koncem:gen',
        'krom':             'kromě:gen',
        'kromě':            'kromě:gen',
        'kvůli':            'kvůli:dat',
        'leda_když':        'ledaže',
        'li_jako':          'li',
        'liž':              'li',
        'mezi_uvnitř':      'uvnitř:gen',
        'na:ins':           'na:acc',
        'na_báze':          'na_bázi:gen',
        'na_čelo':          'na_čele:gen',
        'na_mimo':          'na:loc', # na kurtě i mimo něj
        'na_než':           'na:acc', # na víc než čtyři a půl kilometru
        'na_od':            'na_rozdíl_od:gen',
        'na_počátek':       'na_počátku:gen',
        'na_počest':        'na_počest:gen', # appears also with :dat but the meaning is same
        'na_podklad':       'na_podkladě:gen',
        'na_rozdíl_od':     'na_rozdíl_od:gen',
        'na_strana':        'na_straně:gen',
        'na_účet':          'na_účet:gen',
        'na_újma':          'gen', # 'nebude na újmu' is a multi-word predicate but 'na újmu' is probably not used as an independent oblique modifier
        'na_úroveň':        'na_úrovni:gen',
        'na_úroveň_okolo':  'na_úrovni:gen',
        'na_úsek':          'na_úseku:gen',
        'na_začátek':       'na_začátku:gen',
        'na_základ':        'na_základě:gen',
        'na_základna':      'na_základně:gen',
        'na_závěr':         'na_závěr:gen',
        'na_zda':           'na:loc', # na tom, zda a v jaké formě...
        'namísto':          'namísto:gen',
        'namísto_do':       'do:gen',
        'napospas':         'napospas:dat',
        'narozdíl_od':      'na_rozdíl_od:gen',
        'následek':         'následkem:gen',
        'navzdory':         'navzdory:dat',
        'nedaleko':         'nedaleko:gen',
        'než':              'než', # remove morphological case
        'nežli':            'nežli', # remove morphological case
        'o_jako':           'jako',
        'o_o':              'o:acc',
        'od':               'od:gen',
        'od_počínaje':      'počínaje:ins', # od brambor počínaje a základní zeleninou konče
        'ohledně':          'ohledně:gen',
        'okolo':            'okolo:gen',
        'oproti':           'oproti:dat',
        'po_v':             'po:loc',
        'po_bok':           'po_boku:gen',
        'po_doba':          'po_dobu:gen',
        'po_stránka':       'po_stránce:gen',
        'po_vzor':          'po_vzoru:gen',
        'poblíž':           'poblíž:gen',
        'počátek':          'počátkem:gen',
        'počátkem':         'počátkem:gen',
        'počínaje':         'počínaje:ins',
        'počínat':          'počínaje:ins',
        'počínat_od':       'počínaje:ins',
        'pod_dojem':        'pod_dojmem:gen',
        'pod_tlak':         'pod_tlakem:gen',
        'pod_vliv':         'pod_vlivem:gen',
        'pod_záminka':      'pod_záminkou:gen',
        'pod_záminka_že':   'pod_záminkou_že',
        'podél':            'podél:gen',
        'podle':            'podle:gen',
        'pomoc':            'pomocí:gen',
        'pomocí':           'pomocí:gen',
        'postup':           'postupem:gen',
        'pouze_v':          'v:loc',
        'pro':              'pro:acc',
        'pro_aby':          'pro:acc',
        'prostřednictví':   'prostřednictvím:gen',
        'prostřednictvím':  'prostřednictvím:gen',
        'proti':            'proti:dat',
        'proto_aby':        'aby',
        'protože':          'protože', # remove morphological case
        'před_během':       'během:gen', # před a během utkání
        'před_po':          'po:loc', # před a po vyloučení Schindlera
        'přes':             'přes:acc',
        'přes_přes':        'přes:acc', # annotation error
        'přestože':         'přestože', # remove morphological case
        'při':              'při:loc',
        'při_pro':          'při:loc',
        'při_příležitost':  'při_příležitosti:gen',
        'ruka_v_ruka_s':    'ruku_v_ruce_s:ins',
        's_cíl':            's_cílem', # s cílem projednat X
        's_ohled_k':        's_ohledem_k:dat',
        's_ohled_na':       's_ohledem_na:acc',
        's_pomoc':          's_pomocí:gen',
        's_postup':         'postupem:gen',
        's_přihlédnutí_k':  's_přihlédnutím_k:dat',
        's_přihlédnutí_na': 's_přihlédnutím_na:acc',
        's_výjimka':        's_výjimkou:gen',
        's_výjimka_z':      's_výjimkou:gen',
        's_výjimka_že':     's_výjimkou_že',
        's_vyloučení':      's_vyloučením:gen',
        's_zřetel_k':       'se_zřetelem_k:dat',
        's_zřetel_na':      'se_zřetelem_na:acc',
        'severně_od':       'od:gen',
        'skrz':             'skrz:acc',
        'směr_do':          'směrem_do:gen',
        'směr_k':           'směrem_k:dat',
        'směr_na':          'směrem_na:acc',
        'směr_od':          'směrem_od:gen',
        'směr_přes':        'směrem_přes:acc',
        'směr_z':           'směrem_z:gen',
        'společně_s':       'společně_s:ins',
        'spolu':            'spolu_s:ins',
        'spolu_s':          'spolu_s:ins',
        'spolu_se':         'spolu_s:ins',
        'stranou':          'stranou:gen',
        'stranou_od':       'stranou:gen',
        'takže':            'takže', # remove morphological case
        'takže_a':          'takže',
        'třebaže':          'třebaže', # remove morphological case
        'tvář_v_tvář':      'tváří_v_tvář:dat',
        'u':                'u:gen',
        'u_příležitost':    'u_příležitosti:gen',
        'uprostřed':        'uprostřed:gen',
        'uvnitř':           'uvnitř:gen',
        'v:ins':            'v:loc', # ve skutečností (překlep)
        'v_analogie_s':     'v_analogii_s:ins',
        'v_blízkost':       'v_blízkosti:gen',
        'v_čas':            'v_čase:gen',
        'v_čelo':           'v_čele:gen',
        'v_čelo_s':         'v_čele_s:ins',
        'v_doba':           'v_době:gen',
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
        'v_neprospěch':     'v_neprospěch:gen',
        'v_oblast':         'v_oblasti:gen',
        'v_oblast_s':       's:ins',
        'v_obor':           'v_oboru:gen',
        'v_otázka':         'v_otázce:gen',
        'v_podoba':         'v_podobě:gen',
        'v_poměr_k':        'v_poměru_k:dat',
        'v_porovnání_s':    'v_porovnání_s:ins',
        'v_proces':         'v_procesu:gen',
        'v_prospěch':       've_prospěch:gen',
        'v_protiklad_k':    'v_protikladu_k:dat',
        'v_průběh':         'v_průběhu:gen',
        'v_případ':         'v_případě:gen',
        'v_případ_že':      'v_případě_že',
        'v_rámec':          'v_rámci:gen',
        'v_reakce_na':      'v_reakci_na:acc',
        'v_rozpor_s':       'v_rozporu_s:ins',
        'v_řada':           'v_řadě:gen',
        'v_shoda_s':        've_shodě_s:ins',
        'v_služba':         've_službách:gen',
        'v_směr':           've_směru:gen',
        'v_směr_k':         've_směru_k:dat',
        'v_směr_na':        've_směru_k:dat', # same meaning as ve_směru_na:acc
        'v_smysl':          've_smyslu:gen',
        'v_součinnost_s':   'v_součinnosti_s:ins',
        'v_souhlas_s':      'v_souhlasu_s:ins',
        'v_soulad_s':       'v_souladu_s:ins',
        'v_souvislost_s':   'v_souvislosti_s:ins',
        'v_spojení_s':      've_spojení_s:ins',
        'v_spojení_se':     've_spojení_s:ins',
        'v_spojený_s':      've_spojení_s:ins',
        'v_spojitost_s':    've_spojitosti_s:ins',
        'v_spolupráce_s':   've_spolupráci_s:ins',
        'v_s_spolupráce':   've_spolupráci_s:ins',
        'v_srovnání_s':     've_srovnání_s:ins',
        'v_srovnání_se':    've_srovnání_s:ins',
        'v_stav':           've_stavu:gen',
        'v_stín':           've_stínu:gen',
        'v_světlo':         've_světle:gen',
        'v_úroveň':         'v_úrovni:gen',
        'v_věc':            've_věci:gen',
        'v_vztah_k':        've_vztahu_k:dat',
        'v_vztah_s':        've_vztahu_k:dat',
        'v_zájem':          'v_zájmu:gen',
        'v_záležitost':     'v_záležitosti:gen',
        'v_závěr':          'v_závěru:gen',
        'v_závislost_na':   'v_závislosti_na:loc',
        'v_závislost_s':    'v_závislosti_s:ins',
        'v_znamení':        've_znamení:gen',
        'včetně':           'včetně:gen',
        'vedle':            'vedle:gen',
        'versus':           'versus:nom',
        'vina':             'vinou:gen',
        'vliv':             'vlivem:gen',
        'vlivem':           'vlivem:gen',
        'vůči':             'vůči:dat',
        'výměna_za':        'výměnou_za:acc',
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
        'z_začátek':        'ze_začátku:gen',
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

    @staticmethod
    def compose_edeprel(bdeprel, cdeprel):
        """
        Composes enhanced deprel from the basic part and optional case
        enhancement.

        Parameters
        ----------
        bdeprel : str
            Basic deprel (can include subtype, e.g., 'acl:relcl').
        cdeprel : TYPE
            Case enhancement (can be composed of adposition and morphological
            case, e.g., 'k:dat'). It is optional and it can be None or empty
            string if there is no case enhancement.

        Returns
        -------
        Full enhanced deprel (str).
        """
        edeprel = bdeprel
        if cdeprel:
            edeprel += ':'+cdeprel
        return edeprel

    def process_tree(self, tree):
        """
        Occasionally the edeprels automatically derived from the Czech basic
        trees do not match the whitelist. For example, the noun is an
        abbreviation and its morphological case is unknown.

        We cannot use the process_node() method because it ignores empty nodes.
        """
        for node in tree.descendants_and_empty:
            for edep in node.deps:
                m = re.fullmatch(r'(obl(?::arg)?|nmod|advcl(?::pred)?|acl(?::relcl)?):(.+)', edep['deprel'])
                if m:
                    bdeprel = m.group(1)
                    cdeprel = m.group(2)
                    solved = False
                    # Issues caused by errors in the original annotation must be fixed early.
                    # Especially if acl|advcl occurs with a preposition that unambiguously
                    # receives a morphological case in the subsequent steps, and then gets
                    # flagged as solved.
                    if re.match(r'advcl', bdeprel):
                        # The following advcl should in fact be obl.
                        if re.fullmatch(r'do(?::gen)?', cdeprel): # od nevidím do nevidím ###!!! Ale měli bychom opravit i závislost v základním stromu!
                            bdeprel = 'obl'
                            cdeprel = 'do:gen'
                        elif re.fullmatch(r'k(?::dat)?', cdeprel): ###!!! Ale měli bychom opravit i závislost v základním stromu!
                            bdeprel = 'obl'
                            cdeprel = 'k:dat'
                        elif re.fullmatch(r'místo(?::gen)?', cdeprel): # 'v poslední době se množí bysem místo bych'
                            bdeprel = 'obl'
                            cdeprel = 'místo:gen'
                        elif re.fullmatch(r'od(?::gen)?', cdeprel): # od nevidím do nevidím ###!!! Ale měli bychom opravit i závislost v základním stromu!
                            bdeprel = 'obl'
                            cdeprel = 'od:gen'
                        elif re.fullmatch(r'podle(?::gen)?', cdeprel):
                            bdeprel = 'obl'
                            cdeprel = 'podle:gen'
                        elif re.fullmatch(r's(?::ins)?', cdeprel): ###!!! "seděli jsme tam s Člověče, nezlob se!" Měla by se opravit konverze stromu.
                            bdeprel = 'obl'
                            cdeprel = 's:ins'
                        elif re.fullmatch(r'v_duchu?(?::gen)?', cdeprel):
                            bdeprel = 'obl'
                            cdeprel = 'v_duchu:gen'
                        elif re.fullmatch(r'v', cdeprel):
                            bdeprel = 'obl'
                            cdeprel = 'v:loc'
                        # byl by pro, abychom... ###!!! Opravit i konverzi stromu.
                        elif re.fullmatch(r'pro(?::acc)?', cdeprel):
                            cdeprel = 'aby'
                    elif re.match(r'acl', bdeprel):
                        # The following acl should in fact be nmod.
                        if re.fullmatch(r'k(?::dat)?', cdeprel):
                            bdeprel = 'nmod'
                            cdeprel = 'k:dat'
                        elif re.fullmatch(r'na_způsob(?::gen)?', cdeprel): # 'střídmost na způsob Masarykova "jez dopolosyta"'
                            bdeprel = 'nmod'
                            cdeprel = 'na_způsob:gen'
                        elif re.fullmatch(r'od(?::gen)?', cdeprel):
                            bdeprel = 'nmod'
                            cdeprel = 'od:gen'
                        elif re.fullmatch(r'v', cdeprel):
                            bdeprel = 'nmod'
                            cdeprel = 'v:loc'
                    else: # bdeprel is 'obl' or 'nmod'
                        # The following subordinators should be removed if they occur with nominals.
                        if re.match(r'(ačkoli|když)', cdeprel): # nadějí když ne na zbohatnutí, tak alespoň na dobrou obživu ###!!! perhaps "když" or "když ne" should be analyzed as "cc" here!
                            cdeprel = ''
                        # Removing 'až' must be done early. The remainder may be 'počátek'
                        # and we will want to convert it to 'počátkem:gen'.
                        elif re.match(r'až_(.+):(gen|dat|acc|loc|ins)', cdeprel):
                            cdeprel = re.sub(r'až_(.+):(gen|dat|acc|loc|ins)', r'\1:\2', cdeprel)
                        elif re.fullmatch(r'jestli(?::gen)?', cdeprel): # nevím, jestli osmého nebo devátého září
                            cdeprel = 'gen'
                    edep['deprel'] = self.compose_edeprel(bdeprel, cdeprel)
                    # If one of the following expressions occurs followed by another preposition
                    # or by morphological case, remove the additional case marking. For example,
                    # 'jako_v' becomes just 'jako'.
                    for x in self.outermost:
                        exceptions = self.outermost[x]
                        m = re.fullmatch(x+r'([_:].+)?', cdeprel)
                        if m and m.group(1) and not x+m.group(1) in exceptions:
                            cdeprel = x
                            edep['deprel'] = self.compose_edeprel(bdeprel, cdeprel)
                            solved = True
                            break
                    if solved:
                        continue
                    for x in self.unambiguous:
                        # All secondary prepositions have only one fixed morphological case
                        # they appear with, so we can replace whatever case we encounter with the correct one.
                        m = re.fullmatch(x+r'(?::(?:nom|gen|dat|acc|voc|loc|ins))?', cdeprel)
                        if m:
                            cdeprel = self.unambiguous[x]
                            edep['deprel'] = self.compose_edeprel(bdeprel, cdeprel)
                            solved = True
                            break
                    if solved:
                        continue
                    # The following prepositions have more than one morphological case
                    # available. Thanks to the Case feature on prepositions, we can
                    # identify the correct one.
                    if re.match(r'(obl|nmod)', bdeprel):
                        m = re.fullmatch(r'(mezi|na|nad|o|po|pod|před|v|za)(?::(?:nom|gen|dat|voc))?', cdeprel)
                        if m:
                            adpcase = self.copy_case_from_adposition(node, m.group(1))
                            if adpcase and not re.search(r':(nom|gen|dat|voc)$', adpcase):
                                cdeprel = adpcase
                                edep['deprel'] = self.compose_edeprel(bdeprel, cdeprel)
                                continue
                ###!!! bdeprel and cdeprel are not visible from here on but we may want to use them there as well.
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
                    if edep['deprel'] == 'nmod:loc' and (node.parent == None or node.parent.feats['Case'] == 'Loc') or edep['deprel'] == 'nmod:voc' and node.parent.feats['Case'] == 'Voc':
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
