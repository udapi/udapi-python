"""
Morphosyntactic features (UniDive):
Derive a MS Case feature from morphological case and adposition.
"""
from udapi.core.block import Block
import logging

class MsfCase(Block):

    adposmap = {
        'v+Loc':          'Ine',
        'uvnitř+Gen':     'Ine',
        'uprostřed+Gen':  'Ces',
        'mezi+Ins':       'Int',
        'vně+Gen':        'Ext',
        'na+Loc':         'Ade',
        'v_rámec+Gen':    'Ade', # ???
        'vedle+Gen':      'Apu',
        'u+Gen':          'Chz',
        'kolem+Gen':      'Cir',
        'dokola+Gen':     'Cir',
        'okolo+Gen':      'Cir',
        'v_oblast+Gen':   'Cir',
        'blízko+Dat':     'Prx',
        'blízko+Gen':     'Prx',
        'nedaleko+Gen':   'Prx',
        'daleko+Gen':     'Prx', # lemma of 'nedaleko'
        'poblíž+Gen':     'Prx',
        'daleko_od+Gen':  'Dst',
        'nad+Ins':        'Sup',
        'pod+Ins':        'Sub',
        'vespod+Gen':     'Sub',
        'před+Ins':       'Ant',
        'vpředu+Gen':     'Ant',
        'za+Ins':         'Pst',
        'naproti+Dat':    'Opp',
        'od+Gen':         'Abl',
        'z+Gen':          'Ela',
        'zevnitř+Gen':    'Ela',
        'zprostřed+Gen':  'Cne',
        's+Gen':          'Del',
        'zpod+Gen':       'Sbe',
        'zpoza+Gen':      'Pse',
        'po+Loc':         'Per',
        'napříč+Gen':     'Crs',
        'napříč+Ins':     'Crs',
        'podél+Gen':      'Lng',
        'skrz+Acc':       'Inx',
        'přes+Acc':       'Spx',
        'ob+Acc':         'Cix',
        'po+Acc':         'Ter',
        'do+Gen':         'Ill',
        'dovnitř+Gen':    'Ill',
        'doprostřed+Gen': 'Cnl',
        'mezi+Acc':       'Itl',
        'na+Acc':         'All',
        'k+Dat':          'Apl',
        'nad+Acc':        'Spl',
        'pod+Acc':        'Sbl',
        'před+Acc':       'Anl',
        'za+Acc':         'Psl',
        'dokud':          'Tan',
        'nežli':          'Tan',
        'v+Acc':          'Tem',
        'v_období+Gen':   'Tpx',
        'počátkem+Gen':   'Din',
        'začátkem+Gen':   'Din',
        'během+Gen':      'Dur',
        'postupem+Gen':   'Dur',
        'při+Loc':        'Dur',
        'v_průběh+Gen':   'Dur',
        'za+Gen':         'Der',
        'koncem+Gen':     'Dtr',
        'konec+Gen':      'Dtr',
        'závěrem+Gen':    'Dtr',
        'jakmile':        'Tps',
        'jen_co':         'Tps',
        'počínaje+Ins':   'Teg',
        'jménem+Nom':     'Atr',
        'zdali':          'Atr',
        'že':             'Atr',
        's+Ins':          'Com',
        'spolu_s+Ins':    'Com',
        'společně_s+Ins': 'Com',
        'bez+Gen':        'Abe',
        'včetně+Gen':     'Inc',
        'kromě+Gen':      'Exc',
        'mimo+Acc':       'Exc',
        'mimo+Gen':       'Exc',
        'vyjma+Gen':      'Exc',
        'místo+Gen':      'Sbs',
        'namísto+Gen':    'Sbs',
        'jako':           'Ess',
        'jako+':          'Ess',
        'jako+Nom':       'Ess',
        'jako+Acc':       'Ess',
        'jako+Dat':       'Ess',
        'jako_u+Gen':     'Ess',
        'jako_v+Loc':     'Ess',
        'formou+Gen':     'Ess',
        'oproti+Dat':     'Dsm',
        'na_rozdíl_od+Gen': 'Dsm',
        'než':            'Cmp',
        'než+Nom':        'Cmp',
        'než+Gen':        'Cmp',
        'než+Acc':        'Cmp',
        'než_nad+Ins':    'Cmp',
        'než_v+Acc':      'Cmp',
        'než_v+Loc':      'Cmp',
        'v_srovnání_s+Ins': 'Cmp',
        'o+Acc':          'Dif',
        'kdežto':         'Cmt',
        'přičemž':        'Cmt',
        'zatímco':        'Cmt',
        'díky+Dat':       'Cau',
        'kvůli+Dat':      'Cau',
        'vinou+Gen':      'Cau',
        'vlivem+Gen':     'Cau',
        'vliv+Gen':       'Cau',
        'zásluhou+Gen':   'Cau',
        'zásluha+Gen':    'Cau',
        'v_důsledek+Gen': 'Cau',
        'jelikož':        'Cau',
        'ježto':          'Cau',
        'poněvadž':       'Cau',
        'protože':        'Cau',
        'takže':          'Cau',
        'následek+Gen':   'Cau',
        'aby':            'Pur',
        'na_základ+Gen':  'Cns',
        's_ohled_na+Acc': 'Cns',
        'v_souvislost_s+Ins': 'Cns',
        'v_světlo+Gen':   'Cns',
        'vzhledem_k+Dat': 'Cns',
        'ať':             'Ign',
        'bez_ohled_na+Acc': 'Ign',
        'navzdory+Dat':   'Ccs',
        'vzdor+Dat':      'Ccs',
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
        'v_případ+Gen':   'Cnd',
        'o+Loc':          'The',
        'ohledně+Gen':    'The',
        'stran+Gen':      'The',
        'z_hledisko+Gen': 'The',
        'podle+Gen':      'Quo',
        'dle+Gen':        'Quo',
        'pomocí+Gen':     'Ins',
        'prostřednictvím+Gen': 'Ins',
        'prostřednictví+Gen': 'Ins',
        'pro+Acc':        'Ben',
        'proti+Dat':      'Adv',
        'kontra+Nom':     'Adv',
        'versus+Nom':     'Adv',
        'vůči+Dat':       'Adv',
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
        node.misc['MSFCase'] = msfcase
