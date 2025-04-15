"""
Morphosyntactic features (UniDive):
Derive a MS Case feature from morphological case and adposition.
"""
from udapi.core.block import Block
import logging

class Case(Block):

    adposmap = {
        'v+Loc':          'Ine',
        'uvnitř+Gen':     'Ine',
        'uvnitř+':        'Ine',
        'mezi_uvnitř+Gen': 'Ine', # annotation error?
        'uprostřed+Gen':  'Ces',
        'mezi+Ins':       'Int',
        'mezi+Nom':       'Int', # annotation error
        'mezi+Voc':       'Int', # annotation error
        'vně+Gen':        'Ext',
        'stranou+Gen':    'Ext',
        'stranou+Dat':    'Ext',
        'na+Loc':         'Ade',
        'na_mimo+Loc':    'Ade', # annotation error?
        'na_úroveň+Gen':  'Ade',
        'na_úroveň+':     'Ade',
        'v_proces+Gen':   'Ade', # ???
        'v_rámec+Gen':    'Ade', # ???
        'v_rámec+':       'Ade', # ???
        'v_řada+Gen':     'Ade', # ???
        'z_oblast+Gen':   'Ade', # ???
        'vedle+Gen':      'Apu',
        'u+Gen':          'Chz',
        'kolem+Gen':      'Cir',
        'kol+Gen':        'Cir',
        'dokola+Gen':     'Cir',
        'okolo+Gen':      'Cir',
        'v_oblast+Gen':   'Cir',
        'v_oblast+':      'Cir',
        'blízko+Dat':     'Prx',
        'blízko+Gen':     'Prx',
        'blízko+':        'Prx',
        'nedaleko+Gen':   'Prx',
        'daleko+Gen':     'Prx', # lemma of 'nedaleko'
        'poblíž+Gen':     'Prx',
        'daleko_od+Gen':  'Dst',
        'nad+Ins':        'Sup',
        'pod+Ins':        'Sub',
        'vespod+Gen':     'Sub',
        'před+Ins':       'Ant',
        'vpředu+Gen':     'Ant',
        'na_čelo+Gen':    'Ant',
        'v_čelo+Gen':     'Ant',
        'v_čelo+':        'Ant',
        'za+Ins':         'Pst',
        'naproti+Dat':    'Opp',
        'od+Gen':         'Abl',
        'od+Dat':         'Abl', # annotation error
        'směr_od+Gen':    'Abl',
        'z_strana+Gen':   'Abl',
        'z_strana+':      'Abl',
        'z+Gen':          'Ela',
        'z+Nom':          'Ela', # annotation error
        'z+Dat':          'Ela', # annotation error
        'zevnitř+Gen':    'Ela',
        'zprostřed+Gen':  'Cne',
        's+Gen':          'Del',
        'zpod+Gen':       'Sbe',
        'zpoza+Gen':      'Pse',
        'po+Loc':         'Per',
        'cesta+Gen':      'Per',
        'cesta+Ins':      'Per',
        'napříč+Gen':     'Crs',
        'napříč+Ins':     'Crs',
        'podél+Gen':      'Lng',
        'skrz+Acc':       'Inx',
        'přes+Acc':       'Spx',
        'přes+Nom':       'Spx', # annotation error
        'ob+Acc':         'Cix',
        'po+Acc':         'Ter',
        'po+Nom':         'Ter', # annotation error
        'po+Gen':         'Ter', # annotation error
        'do+Gen':         'Ill',
        'do+Acc':         'Ill', # annotation error
        'do_/+Gen':       'Ill',
        'dovnitř+Gen':    'Ill',
        'doprostřed+Gen': 'Cnl',
        'mezi+Acc':       'Itl',
        'na+Acc':         'All',
        'na+Nom':         'All', # annotation error
        'na+Gen':         'All', # annotation error
        'k+Dat':          'Apl',
        'k+Nom':          'Apl', # annotation error
        'vstříc+Dat':     'Apl',
        'do_oblast+Gen':  'Apl',
        'směr+':          'Apl',
        'směr_k+Dat':     'Apl',
        'směr_k+':        'Apl',
        'směr_na+Acc':    'Apl',
        'v_směr_k+Dat':   'Apl',
        'nad+Acc':        'Spl',
        'nad+Nom':        'Spl', # annotation error
        'pod+Acc':        'Sbl',
        'před+Acc':       'Anl',
        'před+Gen':       'Anl', # annotation error
        'za+Acc':         'Psl',
        'dík_za+Acc':     'Psl', # annotation error?
        'dokud':          'Tan',
        'nežli':          'Tan',
        'v+Acc':          'Tem',
        'v+Nom':          'Tem', # annotation error
        'v+Gen':          'Tem', # annotation error
        'při_příležitost+Gen': 'Tem',
        'současně_s+Ins': 'Tem',
        'u_příležitost+Gen': 'Tem',
        'v_období+Gen':   'Tpx',
        'počátkem+Gen':   'Din',
        'počátek+Gen':    'Din',
        'počínat+Ins':    'Din',
        'počínat+':       'Din',
        'začátkem+Gen':   'Din',
        'začátek+Gen':    'Din',
        'během+Gen':      'Dur',
        'postupem+Gen':   'Dur',
        'postup+Gen':     'Dur',
        'při+Loc':        'Dur',
        'v_průběh+Gen':   'Dur',
        'za+Gen':         'Der',
        'koncem+Gen':     'Dtr',
        'konec+Gen':      'Dtr',
        'k_konec+Gen':    'Dtr',
        'končit+Ins':     'Dtr',
        'závěrem+Gen':    'Dtr',
        'závěr+Gen':      'Dtr',
        'na_závěr+Gen':   'Dtr',
        'v_závěr+Gen':    'Dtr',
        'jakmile':        'Tps',
        'jen_co':         'Tps',
        'před_po+Loc':    'Tps',
        'počínaje+Ins':   'Teg',
        'jménem+Nom':     'Atr',
        'jméno+Nom':      'Atr',
        'zdali':          'Atr',
        'že':             'Atr',
        'z_řada+Gen':     'Gen',
        's+Ins':          'Com',
        's+Nom':          'Com', # annotation error
        'spolu_s+Ins':    'Com',
        'spolu_s+':       'Com',
        'společně_s+Ins': 'Com',
        'společně_s+':    'Com',
        'v_čelo_s+Ins':   'Com',
        'v_spolupráce_s+Ins': 'Com',
        'bez+Gen':        'Abe',
        'včetně+Gen':     'Inc',
        'nad_rámec+Gen':  'Add',
        'kromě+Gen':      'Exc',
        'krom+Gen':       'Exc',
        'mimo+Acc':       'Exc',
        'mimo+Gen':       'Exc',
        'vyjma+Gen':      'Exc',
        'až_na+Acc':      'Exc',
        's_výjimka+Gen':  'Exc',
        's_výjimka+':     'Exc',
        'místo+Gen':      'Sbs',
        'místo+Ins':      'Sbs', # něčím místo něčím jiným
        'místo+Loc':      'Sbs', # annotation error
        'místo_do+Gen':   'Sbs',
        'místo_k+Dat':    'Sbs',
        'místo_na+Acc':   'Sbs',
        'místo_na+':      'Sbs',
        'místo_po+Loc':   'Sbs',
        'místo_v+Acc':    'Sbs',
        'místo_v+':       'Sbs',
        'místo_za+Acc':   'Sbs',
        'namísto+Gen':    'Sbs',
        'namísto_do+Gen': 'Sbs',
        'v_zastoupení+Gen': 'Sbs',
        'výměna_za+Acc':  'Sbs',
        'jako':           'Ess',
        'jako+':          'Ess',
        'jako+Nom':       'Ess',
        'jako+Acc':       'Ess',
        'jako+Dat':       'Ess',
        'jako_u+Gen':     'Ess',
        'jako_v+Loc':     'Ess',
        'formou+Gen':     'Ess',
        'forma+Gen':      'Ess',
        'v_forma+Gen':    'Ess',
        'v_podoba+Gen':   'Ess',
        'v_podoba+':      'Ess',
        'shoda+Gen':      'Equ',
        'v_shoda_s+Ins':  'Equ',
        'do_soulad_s+Ins': 'Sem',
        'na_způsob+Gen':  'Sem',
        'po_vzor+Gen':    'Sem',
        'úměrně+Dat':     'Sem',
        'úměrně_k+Dat':   'Sem',
        'úměrně_s+Ins':   'Sem',
        'v_analogie_s+Ins': 'Sem',
        'v_duch+Gen':     'Sem',
        'v_smysl+Gen':    'Sem',
        'oproti+Dat':     'Dsm',
        'na_rozdíl_od+Gen': 'Dsm',
        'na_rozdíl_od+':  'Dsm',
        'než':            'Cmp',
        'než+Nom':        'Cmp',
        'než+Gen':        'Cmp',
        'než+Acc':        'Cmp',
        'než_nad+Ins':    'Cmp',
        'než_v+Acc':      'Cmp',
        'než_v+Loc':      'Cmp',
        'v_poměr_k+Dat':  'Cmp',
        'v_poměr_k+':     'Cmp',
        'v_porovnání_k+Dat': 'Cmp',
        'v_porovnání_s+Ins': 'Cmp',
        'v_porovnání_s+': 'Cmp',
        'v_srovnání_s+Ins': 'Cmp',
        'v_srovnání_s+':  'Cmp',
        'o+Acc':          'Dif',
        'o+Nom':          'Dif', # annotation error
        'o+Gen':          'Dif', # annotation error
        'o+Dat':          'Dif', # annotation error
        'o_o+Acc':        'Dif', # annotation error
        'kdežto':         'Cmt',
        'přičemž':        'Cmt',
        'zatímco':        'Cmt',
        'díky+Dat':       'Cau',
        'dík+Dat':        'Cau',
        'kvůli+Dat':      'Cau',
        'vinou+Gen':      'Cau',
        'vlivem+Gen':     'Cau',
        'vliv+Gen':       'Cau',
        'vliv+':          'Cau',
        'vinou+Gen':      'Cau',
        'vina+Gen':       'Cau',
        'zásluhou+Gen':   'Cau',
        'zásluha+Gen':    'Cau',
        'z_důvod+Gen':    'Cau',
        'v_důsledek+Gen': 'Cau',
        'jelikož':        'Cau',
        'ježto':          'Cau',
        'poněvadž':       'Cau',
        'protože':        'Cau',
        'takže':          'Cau',
        'následek+Gen':   'Cau',
        'aby':            'Pur',
        'jméno+Gen':      'Pur',
        'pro_případ+Gen': 'Pur',
        'v_jméno+Gen':    'Pur',
        'v_zájem+Gen':    'Pur',
        'za_účel+Gen':    'Pur',
        'na_základ+Gen':  'Cns',
        'pod_vliv+Gen':   'Cns',
        's_ohled_na+Acc': 'Cns',
        's_přihlédnutí_k+Dat': 'Cns',
        's_přihlédnutí_na+Acc': 'Cns',
        'v_souvislost_s+Ins': 'Cns',
        'v_souvislost_s+': 'Cns',
        'v_světlo+Gen':   'Cns',
        'vzhledem_k+Dat': 'Cns',
        'v_soulad_s+Ins': 'Cns',
        'v_soulad_s+':    'Cns',
        'z_titul+Gen':    'Cns',
        'ať':             'Ign',
        'bez_ohled_na+Acc': 'Ign',
        'nehledě_k+Dat':  'Ign',
        'nehledě_na+Acc': 'Ign',
        'navzdory+Dat':   'Ccs',
        'vzdor+Dat':      'Ccs',
        'v_rozpor_s+Ins': 'Ccs',
        'ač':             'Ccs',
        'ačkoli':         'Ccs',
        'byť':            'Ccs',
        'přestože':       'Ccs',
        'třebaže':        'Ccs',
        'jestli':         'Cnd',
        'jestliže':       'Cnd',
        'ledaže':         'Cnd',
        'li':             'Cnd',
        'pakliže':        'Cnd',
        'pokud':          'Cnd',
        'pokud+Nom':      'Cnd',
        'zda':            'Cnd',
        'v_případ+Gen':   'Cnd',
        'v_případ+':      'Cnd',
        'v_závislost_na+Loc': 'Cnd',
        'v_závislost_s+Ins': 'Cnd',
        'o+Loc':          'The',
        'ohledně+Gen':    'The',
        'stran+Gen':      'The',
        'co_do+Gen':      'The',
        'na_téma+Gen':    'The',
        'na_téma+Nom':    'The',
        'na_téma+':       'The',
        'na_úsek+Gen':    'The',
        'po_stránka+Gen': 'The',
        'v_obor+Gen':     'The',
        'v_otázka+Gen':   'The',
        'v_spojení_s+Ins': 'The',
        'v_věc+Gen':      'The',
        'v_vztah_k+Dat':  'The',
        'v_vztah_k+':     'The',
        'v_záležitost+Gen': 'The',
        'v_znamení+Gen':  'The',
        'z_hledisko+Gen': 'The',
        'z_hledisko+':    'The',
        'podle+Gen':      'Quo',
        'dle+Gen':        'Quo',
        'pomocí+Gen':     'Ins',
        's_pomoc+Gen':    'Ins',
        'prostřednictvím+Gen': 'Ins',
        'prostřednictví+Gen': 'Ins',
        'prostřednictví+Ins': 'Ins', # annotation error
        'prostřednictví+': 'Ins',
        'za_pomoc+Gen':   'Ins',
        'pro+Acc':        'Ben',
        'pro+Nom':        'Ben', # annotation error
        'pro+Gen':        'Ben', # annotation error
        'pro+Ins':        'Ben', # annotation error
        'napospas+Dat':   'Ben',
        'k_prospěch+Gen': 'Ben',
        'na_úkor+Gen':    'Ben',
        'na_vrub+Gen':    'Ben',
        'v_prospěch+Gen': 'Ben',
        'v_neprospěch+Gen': 'Ben',
        'v_služba+Gen':   'Ben',
        'proti+Dat':      'Adv',
        'proti+Gen':      'Adv',
        'kontra+Nom':     'Adv',
        'versus+Nom':     'Adv',
        'vůči+Dat':       'Adv',
        # subordinators
        'dokud':          'Tan',
        'nežli':          'Tan',
        'jakmile':        'Tps',
        'jen_co':         'Tps',
        'zdali':          'Atr',
        'že':             'Atr',
        'jako':           'Ess',
        'než':            'Cmp',
        'kdežto':         'Cmt',
        'přičemž':        'Cmt',
        'zatímco':        'Cmt',
        'jelikož':        'Cau',
        'ježto':          'Cau',
        'poněvadž':       'Cau',
        'protože':        'Cau',
        'takže':          'Cau',
        'aby':            'Pur',
        'ať':             'Ign',
        'ač':             'Ccs',
        'ačkoli':         'Ccs',
        'byť':            'Ccs',
        'přestože':       'Ccs',
        'třebaže':        'Ccs',
        'jestli':         'Cnd',
        'jestliže':       'Cnd',
        'ledaže':         'Cnd',
        'li':             'Cnd',
        'pakliže':        'Cnd',
        'pokud':          'Cnd',
        'zda':            'Cnd',
        # coordinators
        'a':              'Conj',
        'i':              'Conj',
        'ani':            'Nnor',
        'nebo':           'Disj',
        'či':             'Disj',
        'ale':            'Advs',
        'avšak':          'Advs',
        'však':           'Advs',
        'nýbrž':          'Advs',
        'neboť':          'Reas',
        'tedy':           'Cnsq',
        'tak':            'Cnsq'
    }

    def process_node(self, node):
        """
        Derives a case value from preposition and morphological case. Stores it
        as MSFCase in MISC.
        """
        # Do not do anything for function words.
        # Specifically for Case, also skip 'det' and 'amod' modifiers (congruent attributes)
        # because their Case is only agreement feature inherited from the head noun.
        if node.udeprel in ['case', 'mark', 'cc', 'aux', 'cop', 'punct']:
            node.misc['MSFFunc'] = 'Yes'
            return
        elif node.udeprel in ['det', 'amod']:
            node.misc['MSFFunc'] = 'No'
            return
        else:
            node.misc['MSFFunc'] = 'No'
        # Get all case markers (adpositions) attached to the current node.
        adpositions = []
        for c in node.children:
            if c.udeprel == 'case':
                lemma = c.lemma
                # If it has outgoing 'fixed' relations, it is a multiword adposition.
                fixedchildren = [x.lemma for x in c.children if x.udeprel == 'fixed']
                if fixedchildren:
                    lemma += '_' + '_'.join(fixedchildren)
                adpositions.append(lemma)
        # We assume that all features were copied from FEATS to MISC in mwe.MsfInit.
        # They may have been further processed there, so we take the input from there.
        msfcase = node.misc['MSFCase']
        if adpositions:
            adpostring = '_'.join(adpositions)
            caseadpostring = adpostring + '+' + msfcase
            if caseadpostring in self.adposmap:
                msfcase = self.adposmap[caseadpostring]
            else:
                logging.warn(f"No Case value found for '{caseadpostring}'.")
                msfcase = caseadpostring
        # Omer wants to collect cases from both adpositions and subordinators
        # but we will consider subordinators only if we do not have any case
        # from morphology or adpositions.
        if not msfcase:
            subordinators = []
            for c in node.children:
                if c.udeprel == 'mark':
                    lemma = c.lemma
                    # If it has outgoing 'fixed' relations, it is a multiword adposition.
                    fixedchildren = [x.lemma for x in c.children if x.udeprel == 'fixed']
                    if fixedchildren:
                        lemma += '_' + '_'.join(fixedchildren)
                    subordinators.append(lemma)
            if subordinators:
                subordstring = '_'.join(subordinators)
                if subordstring in self.adposmap:
                    msfcase = self.adposmap[subordstring]
        # To lump coordinators with all the above makes even less sense but for
        # the moment we do it.
        if not msfcase:
            coordinators = []
            for c in node.children:
                if c.udeprel == 'cc':
                    lemma = c.lemma
                    # If it has outgoing 'fixed' relations, it is a multiword adposition.
                    fixedchildren = [x.lemma for x in c.children if x.udeprel == 'fixed']
                    if fixedchildren:
                        lemma += '_' + '_'.join(fixedchildren)
                    coordinators.append(lemma)
            if coordinators:
                coordstring = '_'.join(coordinators)
                if coordstring in self.adposmap:
                    msfcase = self.adposmap[coordstring]
        node.misc['MSFCase'] = msfcase
