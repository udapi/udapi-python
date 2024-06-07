"""Block to fix case-enhanced dependency relations in Arabic."""
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
        'أَنَّ':  [],
        'أَن':  [],
        'إِنَّ':  [],
        'إِذَا': [],
        'حَيثُ': [],
        'مِثلَ': [],
        'لِأَنَّ':  [],
        'كَمَا': []
    }

    # Secondary prepositions sometimes have the lemma of the original part of
    # speech. We want the grammaticalized form instead. List even those that
    # will have the same lexical form, as we also want to check the morphological
    # case. And include all other prepositions that have unambiguous morphological
    # case, even if they are not secondary.
    unambiguous = {
        'فِي':    'فِي:gen', # fī = in
        'لِ':     'لِ:gen', # li = to
        'مِن':    'مِن:gen', # min = from
        'بِ':     'بِ:gen', # bi = for, with
        'عَلَى':   'عَلَى:gen', # ʿalā = on
        'إِلَى':   'إِلَى:gen', # ʾilā = to
        'بَينَ':   'بَينَ:gen', # bayna = between
        'مَعَ':    'مَعَ:gen', # maʿa = with
        'عَن':    'عَن:gen', # ʿan = about, from
        'خِلَالَ':   'خِلَالَ:gen', # ḫilāla = during
        'بَعدَ':   'بَعدَ:gen', # baʿda = after
        'بَعدَمَا': 'بَعدَ:gen', # baʿdamā = after
        'بَعدَ_أَن': 'بَعدَ:gen', # baʿda ʾan = after + clause
        'مُنذُ':   'مُنذُ:gen', # munḏu = since
        'حَولَ':   'حَولَ:gen', # ḥawla = about
        'أَنَّ':    'أَنَّ', # remove morphological case; ʾanna = that
        'أَن':    'أَن', # remove morphological case; ʾan = that
        'إِنَّ':    'إِنَّ', # remove morphological case; ʾinna = that
        'قَبلَ':   'قَبلَ:gen', # qabla = before
        'أَمَامَ':  'أَمَامَ:gen', # ʾamāma = in front of
        'إِذَا':   'إِذَا', # remove morphological case; ʾiḏā = if
        'بِ_سَبَب': 'بِسَبَبِ:gen', # bisababi = because of
        'حَيثُ':   'حَيثُ', # remove morphological case; ḥayṯu = where (SCONJ, not ADV)
        'مِن_خِلَالَ': 'مِن_خِلَالِ:gen', # min ḫilāli = through, during
        'حَتَّى':   'حَتَّى:gen', # ḥattā = until
        'دَاخِلَ':  'دَاخِلَ:gen', # dāḫila = inside of
        'لَدَى':   'لَدَى:gen', # ladā = with, by, of, for
        'ضِدَّ':    'ضِدَّ:gen', # ḍidda = against
        'مِن_أَجل': 'مِن_أَجلِ:gen', # min ʾaǧli = for the sake of
        'مِثلَ':   'مِثلَ', # remove morphological case; miṯla = like
        'لِأَنَّ':    'لِأَنَّ', # remove morphological case; li-ʾanna = because
        'كَ':     'كَ:gen', # ka = in (temporal?)
        'عِندَمَا': 'عِندَمَا', # ʿindamā = when
        'عِندَ':   'عِندَمَا', # ʿinda = when
        'تَحتَ':   'تَحتَ:gen', # tahta = under
        'عَبرَ':   'عَبرَ:gen', # ʿabra = via
        'كَمَا':   'كَمَا', # remove morphological case; kamā = as
        'مُقَابِلَ': 'مُقَابِلَ:gen', # muqābila = in exchange for, opposite to, corresponding to
        'فِي_إِطَار': 'فِي_إِطَار:gen', # fī ʾiṭār = in frame
        'virš':             'virš:gen' # above
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
                # Arabic clauses often start with وَ wa "and", which does not add
                # much to the meaning but sometimes gets included in the enhanced
                # case label. Remove it if there are more informative subsequent
                # morphs.
                edep['deprel'] = re.sub(r':وَ_', r':', edep['deprel'])
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
                # identify the correct one. Exclude 'nom' and 'voc', which cannot
                # be correct.
                m = re.match(r'^(obl(?::arg)?|nmod):(po|už)(?::(?:nom|voc))?$', edep['deprel'])
                if m:
                    adpcase = self.copy_case_from_adposition(node, m.group(2))
                    if adpcase and not re.search(r':(nom|voc)$', adpcase):
                        edep['deprel'] = m.group(1)+':'+adpcase
                        continue
                    # The remaining instance of 'po' should be ':acc'.
                    elif m.group(2) == 'po':
                        edep['deprel'] = m.group(1)+':po:acc'
                        continue
                    # The remaining 'už' are ':acc' (they are second conjuncts
                    # in coordinated oblique modifiers).
                    elif m.group(2) == 'už':
                        edep['deprel'] = m.group(1)+':už:acc'
                        continue

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
