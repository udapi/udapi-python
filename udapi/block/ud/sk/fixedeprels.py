"""Block to fix case-enhanced dependency relations in Slovak."""
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
        'do':              'do:gen',
        'k':               'k:dat',
        'mimo':            'mimo:gen',
        'na_rozdiel_od':   'na_rozdiel_od:gen',
        'na_základ':       'na_základe:gen',
        'od':              'od:gen',
        'pomoc':           'pomocou:gen',
        'pre':             'pre:acc',
        'prostredníctvom': 'prostredníctvom:gen',
        's':               's:ins',
        's_dôraz_na':      's_dôrazom_na:acc',
        's_ohľad_na':      's_ohľadom_na:acc',
        's_pomoc':         's_pomocou:gen',
        'smer_k':          'smerom_k:dat',
        'spoločne_s':      'spoločne_s:ins',
        'spolu_s':         'spolu_s:ins',
        'v_dôsledok':      'v_dôsledku:gen',
        'v_meno':          'v_mene:gen',
        'v_oblasť':        'v_oblasti:gen',
        'v_porovnanie_s':  'v_porovnaniu_s:ins',
        'v_priebeh':       'v_priebehu:gen',
        'v_prípad':        'v_prípade:gen',
        'v_prospech':      'v_prospech:gen',
        'v_rámec':         'v_rámci:gen',
        'v_spolupráca_s':  'v_spolupráci_s:ins',
        'v_súlad_s':       'v_súlade_s:ins',
        'v_súvislosť_s':   'v_súvislosti_s:ins',
        'v_ústrety':       'v_ústrety:dat',
        'v_vzťah_k':       'vo_vzťahu_k:dat',
        'v_závislosť_na':  'v_závislosti_na:loc',
        'vzhľad_na':       'vzhľadom_na:acc',
        'z':               'z:gen',
        'z_hľadisko':      'z_hľadiska:gen',
        'začiatkom':       'začiatkom:gen'
    }

    def process_node(self, node):
        """
        Occasionally the edeprels automatically derived from the Slovak basic
        trees do not match the whitelist. For example, the noun is an
        abbreviation and its morphological case is unknown.
        """
        for edep in node.deps:
            for x, xnorm in unambiguous:
                # All secondary prepositions have only one fixed morphological case
                # they appear with, so we can replace whatever case we encounter with the correct one.
                m = re.match(r'^(obl(?::arg)?|nmod|advcl|acl):'+x+r'(?::(?:nom|gen|dat|acc|voc|loc|ins))?$', edep['deprel'])
                if m:
                    edep['deprel'] = m.group(0)+':'+xnorm
                    break

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
