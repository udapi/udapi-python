"""
Morphosyntactic features (UniDive):
Derive a MS Case feature from morphological case and adposition.
"""
from udapi.core.block import Block

class MsfCase(Block):

    adposmap = {
        'v+Loc':          'Ine',
        'uvnitř+Gen':     'Ine',
        'uprostřed+Gen':  'Ces',
        'mezi+Ins':       'Int',
        'vně+Gen':        'Ext',
        'na+Loc':         'Ade',
        'vedle+Gen':      'Apu',
        'u+Gen':          'Chz',
        'kolem+Gen':      'Cir',
        'dokola+Gen':     'Cir',
        'okolo+Gen':      'Cir',
        'blízko+Dat':     'Prx',
        'blízko+Gen':     'Prx',
        'nedaleko+Gen':   'Prx',
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
        'počátkem+Gen':   'Din',
        'začátkem+Gen':   'Din',
        'během+Gen':      'Dur',
        'postupem+Gen':   'Dur',
        'při+Loc':        'Dur',
        'za+Gen':         'Der',
        'koncem+Gen':     'Dtr',
        'závěrem+Gen':    'Dtr',
        'jakmile':        'Tps',
        'jen_co':         'Tps',
        'počínaje+Ins':   'Teg',
        'jménem+Nom':     'Atr',
        'zdali':          'Atr',
        'že':             'Atr',
        's+Ins':          'Com',
        'bez+Gen':        'Abe',
        'včetně+Gen':     'Inc',
        'kromě+Gen':      'Exc',
        'mimo+Acc':       'Exc',
        'mimo+Gen':       'Exc',
        'vyjma+Gen':      'Exc',
        'místo+Gen':      'Sbs',
        'namísto+Gen':    'Sbs',
        'jako':           'Ess',
        'formou+Gen':     'Ess',
        'oproti+Dat':     'Dsm',
        'než':            'Cmp',
        'o+Acc':          'Dif',
        'kdežto':         'Cmt',
        'přičemž':        'Cmt',
        'zatímco':        'Cmt',
        'kvůli+Dat':      'Cau',
        'vinou+Gen':      'Cau',
        'vlivem+Gen':     'Cau',
        'zásluhou+Gen':   'Cau',
        'jelikož':        'Cau',
        'ježto':          'Cau',
        'poněvadž':       'Cau',
        'protože':        'Cau',
        'takže':          'Cau',
        'aby':            'Pur',
        'ať':             'Ign',
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
        'o+Loc':          'The',
        'stran+Gen':      'The',
        'podle+Gen':      'Quo',
        'dle+Gen':        'Quo',
        'pomocí+Gen':     'Ins',
        'prostřednictvím+Gen': 'Ins',
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
        if node.udeprel in ['case', 'mark', 'cc', 'aux', 'cop']:
            node.misc['MSFFunc'] = 'Yes'
            return
        else:
            node.misc['MSFFunc'] = 'No'
        adpositions = [x.lemma for x in node.children if x.udeprel == 'case']
        msfcase = node.feats['Case']
        if adpositions:
            adpostring = '_'.join(adpositions)
            caseadpostring = adpostring + '+' + msfcase
            if caseadpostring in adposmap:
                msfcase = adposmap[caseadpostring]
            else:
                msfcase = caseadpostring
        node.misc['MSFCase'] = msfcase
