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
        'لَو':  [],
        'حَيثُ': [],
        'مِثلَ': [],
        'لِأَنَّ':  [],
        'كَمَا': [],
        'فِي_حِينَ': []
    }

    # Secondary prepositions sometimes have the lemma of the original part of
    # speech. We want the grammaticalized form instead. List even those that
    # will have the same lexical form, as we also want to check the morphological
    # case. And include all other prepositions that have unambiguous morphological
    # case, even if they are not secondary.
    unambiguous = {
        'فِي':            'فِي:gen', # fī = in
        'لِ':             'لِ:gen', # li = to
        'مِن':            'مِن:gen', # min = from
        'بِ':             'بِ:gen', # bi = for, with
        'عَلَى':           'عَلَى:gen', # ʿalā = on
        'عَلَى_أَن':        'عَلَى:gen', # ʿalā = on
        'عَلَى_أَنَّ':        'عَلَى:gen', # ʿalā = on
        'عَلَى_أَنَّ_هُوَ':     'عَلَى:gen', # ʿalā = on
        'عَلَى_أَن_بِ':      'عَلَى:gen', # ʿalā = on
        'عَلَى_أَنَّ_هُوَ_لَدَى': 'عَلَى:gen', # ʿalā = on
        'عَلَى_أَنَّ_مِن_شَأن': 'عَلَى:gen', # ʿalā = on
        'إِلَى':       'إِلَى:gen', # ʾilā = to
        'بَينَ':       'بَينَ:gen', # bayna = between
        'بَينَمَا':     'بَينَ:gen',
        'بَينَمَا_لَم':  'بَينَ:gen',
        'مِن_بَينَ':    'بَينَ:gen',
        'مَعَ_مِن_بَينَ': 'بَينَ:gen',
        'مِن_مِن_بَينَ': 'بَينَ:gen',
        'مَعَ':        'مَعَ:gen', # maʿa = with
        'عَن':       'عَن:gen', # ʿan = about, from
        'خِلَالَ':      'خِلَالَ:gen', # ḫilāla = during
        'بَعدَ':      'بَعدَ:gen', # baʿda = after
        'بَعدَمَا':    'بَعدَ:gen', # baʿdamā = after
        'بَعدَ_أَن':   'بَعدَ:gen', # baʿda ʾan = after + clause
        'مُنذُ':      'مُنذُ:gen', # munḏu = since
        'حَولَ':      'حَولَ:gen', # ḥawla = about
        'أَنَّ':       'أَنَّ', # remove morphological case; ʾanna = that
        'أَن':       'أَنَّ', # remove morphological case; ʾanna = that
        'إِنَّ':       'إِنَّ', # remove morphological case; ʾinna = that
        'إِن':       'إِنَّ', # remove morphological case; ʾinna = that
        'قَبلَ':      'قَبلَ:gen', # qabla = before
        'قَبلَ_أَن':   'قَبلَ:gen', # qabla = before
        'أَمَامَ':    'أَمَامَ:gen', # ʾamāma = in front of
        'إِذَا':     'إِذَا', # remove morphological case; ʾiḏā = if
        'بِ_سَبَب':   'بِسَبَبِ:gen', # bisababi = because of
        'حَيثُ':     'حَيثُ', # remove morphological case; ḥayṯu = where (SCONJ, not ADV)
        'مِن_خِلَالَ':  'مِن_خِلَالِ:gen', # min ḫilāli = through, during
        'حَتَّى':     'حَتَّى:gen', # ḥattā = until
        'دَاخِلَ':    'دَاخِلَ:gen', # dāḫila = inside of
        'لَدَى':     'لَدَى:gen', # ladā = with, by, of, for
        'ضِدَّ':      'ضِدَّ:gen', # ḍidda = against
        'مِن_أَجل':           'مِن_أَجلِ:gen', # min ʾaǧli = for the sake of
        'مِن_اجل':           'مِن_أَجلِ:gen', # min ʾaǧli = for the sake of
        'مِثلَ':     'مِثلَ', # remove morphological case; miṯla = like
        'لِأَنَّ':      'لِأَنَّ', # remove morphological case; li-ʾanna = because
        'كَ':       'كَ:gen', # ka = in (temporal?)
        'عِندَمَا':   'عِندَمَا', # ʿindamā = when
        'عِندَ':     'عِندَمَا', # ʿinda = when
        'تَحتَ':     'تَحتَ:gen', # tahta = under
        'عَبرَ':     'عَبرَ:gen', # ʿabra = via
        'كَمَا':     'كَمَا', # remove morphological case; kamā = as
        'مُقَابِلَ':   'مُقَابِلَ:gen', # muqābila = in exchange for, opposite to, corresponding to
        'فِي_إِطَار': 'فِي_إِطَار:gen', # fī ʾiṭār = in frame
        'فِي_حِينَ':  'فِي_حِينِ', # fī ḥīni = while
        'فِيمَا':    'فِيمَا', # fīmā = while
        'ضِمنَ':     'ضِمنَ:gen', # ḍimna = within, inside, among
        'مِن_دُونَ':  'مِن_دُونِ:gen', # min dūni = without, beneath, underneath
        'مِن_دُونَ_أَن': 'مِن_دُونِ:gen', # min dūni ʾan = without, beneath, underneath + clause
        'دُونَ':     'دُونَ:gen', # dūna = without
        'بِ_دُونَ':   'دُونَ:gen', # bi dūni = without
        'دُونَ_أَن':  'دُونَ:gen', # dūna ʾan = without
        'بِ_دُونَ_أَن': 'دُونَ:gen', # bi dūni ʾan = without
        'دُونَ_سِوَى': 'دُونَ:gen', # dūna siwā = without
        'إِثرَ':     'إِثرَ:gen', # ʾiṯra = right after
        'عَلَى_إِثرَ': 'إِثرَ:gen', # ʿalā ʾiṯri = right after
        'رَغمَ':     'رَغمَ:gen', # raġma = despite
        'رَغمَ_أَنَّ':  'رَغمَ:gen', # raġma ʾanna = despite + clause
        'عَلَى_رَغمَ_أَنَّ': 'رَغمَ:gen', # ʿalā raġma ʾanna = despite + clause
        'رَغمَ_أَنَّ_مِن': 'رَغمَ:gen', # raġma ʾanna min = despite
        'إِلَى_أَنَّ':    'إِلَى_أَنَّ', # until? that?
        'إِلَى_أَنَّ_هُوَ': 'إِلَى_أَنَّ',
        'إِلَى_أَنَّ_لَدَى': 'إِلَى_أَنَّ',
        'إِلَى_أَنَّ_هُوَ_مِن': 'إِلَى_أَنَّ',
        'بِ_إِضَافَة_إِلَى_أَنَّ': 'إِلَى_أَنَّ',
        'إِلَى_أَنَّ_هُوَ_مِن_بَينَ': 'إِلَى_أَنَّ',
        'إِلَى_أَنَّ_مِن':        'إِلَى_أَنَّ',
        'نَحوَ':              'نَحوَ', # naḥwa = about, approximately
        'بِ_نَحوَ':            'بِ:gen', # by about N
        'نَحوَ_بِ':            'بِ:gen', # about by N
        'قَبلَ_نَحوَ':          'قَبلَ:gen', # before about N
        'عَلَى_نَحوَ':          'عَلَى:gen', # to about N
        'إِلَى_نَحوَ':          'إِلَى:gen', # to about N
        'لِ_نَحوَ':            'لِ:gen', # to/for about N
        'مُنذُ_نَحوَ':          'مُنذُ:gen', # since about N
        'بَعدَ_نَحوَ':          'بَعدَ:gen', # after about N
        'فِي_نَحوَ':           'فِي:gen', # in about N
        'أَثنَاءَ':            'أَثنَاءَ:gen', # ʾaṯnāʾa = during
        'فِي_أَثنَاءَ':         'أَثنَاءَ:gen', # ʾaṯnāʾa = during
        'لَو':               'لَو', # law = if
        'حَتَّى_لَو':           'لَو', # even if
        'حَتَّى_وَ_لَو':         'لَو', # even if
        'لَو_أَنَّ':            'لَو', # if
        'لَو_مِن':            'لَو', # if
        'بِ_أَنَّ':             'أَنَّ', # that
        'بِ_أَنَّ_هما_مِن':      'أَنَّ', # that
        'بِ_أَنَّ_هُوَ':          'أَنَّ', # that
        'بِ_أَنَّ_أَمَامَ':        'أَنَّ', # that
        'بِ_أَنَّ_لَا':           'أَنَّ', # that
        'بِ_أَنَّ_هُوَ_عَلَى':      'أَنَّ', # that
        'بِ_أَنَّ_لَا':           'أَنَّ', # that
        'بِ_أَنَّ_مِن':          'أَنَّ', # that
        'عَقِبَ':              'عَقِبَ:gen', # ʿaqiba = following
        'عَقِبَ_أَن':           'عَقِبَ:gen', # ʿaqiba = following
        'عَقِبَ_مِن':           'عَقِبَ:gen', # ʿaqiba = following
        'إِذ':               'إِذ', # ʾiḏ = because
        'إِذ_أَنَّ':            'إِذ', # ʾiḏ ʾanna
        'بِ_شَأن':            'بِشَأنِ:gen', # bišaʾni = about, regarding (lit. with + matter)
        'حَسَبَ':              'حَسَبَ:gen', # ḥasaba = according to, depending on
        'بِ_حَسَبَ':            'حَسَبَ:gen', # ḥasaba = according to, depending on
        'حَسَبَمَا':            'حَسَبَ:gen', # ḥasaba = according to, depending on
        'عَلَى_حَسَبَ':          'حَسَبَ:gen', # ḥasaba = according to, depending on
        'بِ_نِسبَة_لِ':         'بِاَلنِّسبَةِ_لِ:gen', # bi an-nisbati li (bin-nisbati li) = in proportion/relation to
        'بِ_نِسبَة_لِ_مِن':      'بِاَلنِّسبَةِ_لِ:gen', # bi an-nisbati li (bin-nisbati li) = in proportion/relation to
        'بِ_نِسبَة_إِلَى':       'بِاَلنِّسبَةِ_لِ:gen', # bi an-nisbati ʾilā (bin-nisbati ʾilā) = in proportion/relation to
        'بِ_نِسبَة':           'بِاَلنِّسبَةِ_لِ:gen', # bi an-nisbati (bin-nisbati) = in proportion/relation to
        'تُجَاهَ':             'تُجَاهَ:gen', # tuǧāha = towards, facing
        'لِكَي':              'لِكَي', # li-kay = in order to
        'ذٰلِكَ_لِكَي':          'لِكَي', # li-kay = in order to
        'كَي':               'لِكَي', # kay = in order to
        'مِن_قِبَل':           'مِن_قِبَلِ:gen', # min qibali = by
        'مِن_قِبَل_بِ_فِي':      'مِن_قِبَلِ:gen', # min qibali = by
        'حَوَالَى':            'حَوَالَى', # ḥawālā = around, about
        'فِي_حَوَالَى':         'فِي:gen', # fi hawala = in around X
        'إِلَى_حَوَالَى':        'إِلَى:gen', # ila hawala = to around X
        'بِ_حَوَالَى':          'بِ:gen', # bi hawala = with around X
        'حَوَالَى_مِن':         'مِن:gen', # hawala min = from around X
        'مِن_حَوَالَى':         'مِن:gen', # min hawala = from around X
        'بَينَ_حَوَالَى':        'بَينَ:gen', # bayna hawala
        'مُقَابِلَ_حَوَالَى':      'مُقَابِلَ:gen', # muqabila hawala
        'إِلَى_حَوَالَى_مِن':     'إِلَى:gen', # ila hawala min
        'لِ_حَوَالَى':          'لِ:gen', # li hawala = for around X
        'بَعدَ_حَوَالَى':        'بَعدَ:gen', # baada hawala
        'قَبلَ_حَوَالَى':        'قَبلَ:gen', # qabla hawala
        'خَارِجَ':             'خَارِجَ:gen', # ḫāriǧa = outside
        'فِي_خَارِجَ':          'خَارِجَ:gen', # ḫāriǧa = outside
        'لِ_خَارِجَ':           'لِخَارِجِ:gen', # liḫāriǧi = out
        'إِلَى_خَارِجَ':         'إِلَى_خَارِجِ:gen', # ʾilā ḫāriǧi = out
        'مِن_خَارِجَ':          'مِن_خَارِجِ:gen', # min ḫāriǧi = from outside
        'عَلَى_رَغم':          'عَلَى_رَغمِ:gen', # ʿalā raġmi = despite
        'عَلَى_رَغم_مِن':       'عَلَى_رَغمِ:gen', # ʿalā raġmi = despite
        'عَلَى_رَغم_أَنَّ':       'عَلَى_رَغمِ:gen', # ʿalā raġmi = despite
        'عَلَى_رَغم_مِن_أَنَّ':    'عَلَى_رَغمِ:gen', # ʿalā raġmi = despite
        'عَلَى_رَغم_مِن_أَنَّ_هُوَ': 'عَلَى_رَغمِ:gen', # ʿalā raġmi = despite
        'وَسطَ':              'وَسطَ:gen', # wasṭa = in the middle
        'فِي_وَسطَ':           'وَسطَ:gen', # wasṭa = in the middle
        'بِ_وَسطَ':            'وَسطَ:gen', # wasṭa = in the middle
        'وِفقَ':              'وِفقَ:gen', # wifqa = according to
        'إِزَاءَ':             'إِزَاءَ:gen', # ʾizāʾa = regarding, facing, towards
        'بِ_إِزَاءَ':           'إِزَاءَ:gen', # ʾizāʾa = regarding, facing, towards
        'قُربَ':              'قُربَ:gen', # qurba = near
        'عَن_قُربَ':           'قُربَ:gen', # qurba = near
        'وَرَاءَ':             'وَرَاءَ:gen', # warāʾa = behind, past, beyond
        'عَن_أَنَّ_وَرَاءَ':       'وَرَاءَ:gen', # warāʾa = behind, past, beyond
        'مِن_وَرَاءَ':          'مِن_وَرَاءِ:gen', # min warāʾi = from behind
        'بِ_إِضَافَة_إِلَى':      'بِاَلإِضَافَةِ_إِلَى:gen', # bi-al-ʾiḍāfati ʾilā = in addition to
        'فَوقَ':              'فَوقَ:gen', # fawqa = above, over
        'مِن_فَوقَ':           'مِن_فَوقِ:gen', # min fawqi = from above
        'إِلَى_جَانِب':         'إِلَى_جَانِبِ:gen', # ʾilā ǧānibi = beside
        'مِن_جَانِب':          'إِلَى_جَانِبِ:gen', # min ǧānibi = beside
        'بِ_هَدَف':            'بِهَدَفِ:gen', # bihadafi = with goal
        'بِ_اِسم':            'بِاِسمِ:gen', # biismi = in name of
        'مِن_حَيثُ':           'مِن:gen',
        'بِ_حَيثُ':            'بِ:gen',
        'فِي_حُضُور':          'فِي_حُضُورِ:gen', # fī ḥuḍūri = in presence of
        'بِ_خِلَاف':            'بِخِلَافِ:gen', # biḫilāfi = in addition to
        'جَرَّاء':             'جَرَّاء:gen', # ǧarrāʾ = because of
        'مِن_جَرَّاء':          'جَرَّاء:gen', # ǧarrāʾ = because of
        'عَن_طَرِيق':          'عَن_طَرِيقِ:gen', # ʿan ṭarīqi = via
        'فِي_ظِلّ':            'فِي_ظِلِّ:gen', # fī ẓilli = in light of
        'بِ_مُوجِب':           'بِمُوجِبِ:gen', # bimūǧibi = with motive
        'حِيَالَ':             'حِيَالَ:gen', # ḥiyāla = concerning
        'فِي_شَأن':           'فِي_شَأنِ:gen', # fī šaʾni = in regard of
        'فِي_عُقب':           'فِي_أَعقَابِ:gen', # fī ʾaʿqābi = in the aftermath of
        'بناء_عَلَى':         'بناء_عَلَى:gen', # bnāʾ ʿalā = based on
        'طِوَالَ':             'طِوَالَ:gen', # ṭiwāla = throughout
        'فِي_حِين_أَنَّ':        'فِي_حِينِ',
        'فِي_غُضُون':          'فِي:gen',
        'فِي_مُقَابِلَ':         'مُقَابِلَ:gen',
        'لِ_بِ':              'لِ:gen',
        'بِ_لَا':              'بِ:gen',
        'لِ_صَالِح':           'لِصَالِحِ:gen', # liṣāliḥi = in interest of
        'سِوَى':              'سِوَى:gen', # siwā = except for
        'سِوَى_عَلَى':          'سِوَى:gen', # siwā = except for
        'سِوَى_أَنَّ_هُوَ':        'سِوَى:gen', # siwā = except for
        'سِوَى_بِ':            'سِوَى:gen', # siwā = except for
        'سِوَى_لِ':            'سِوَى:gen', # siwā = except for
        'بِ_اِستِثنَاء':        'بِاِستِثنَاءِ:gen', # biistiṯnāʾi = with exception of
        'بِ_قُرب_مِن':         'بِاَلقُربِ_مِن:gen', # bi-al-qurbi min = near (with proximity to)
        'قُبَالَةَ':            'قُبَالَةَ:gen', # qubālata = in front of, facing
        'إِلَى_أَن':           'إِلَى:gen',
        'بِ_إِلَى':            'بِ:gen',
        'بِ_إِنَّ':             'بِ:gen',
        'بِ_رَغم_مِن_أَن':      'بِ:gen',
        'بِ_رَغم_مِن_أَنَّ_هُوَ':   'بِ:gen',
        'بِ_عَلَى':            'بِ:gen',
        'بِ_عَن':             'بِ:gen',
        'بِ_فِي':             'بِ:gen',
        'بِ_كَ':              'بِ:gen',
        'بِ_لِ':              'بِ:gen',
        'بِ_مَا_أَنَّ':          'بِ:gen',
        'بِ_مِن':             'بِ:gen',
        'بِ_وَ_لِ':            'بِ:gen',
        'عَلَى_إِلَى':          'عَلَى:gen',
        'عَلَى_بِ':            'عَلَى:gen',
        'عَلَى_بِ_فِي':         'عَلَى:gen',
        'عَلَى_مِن':           'عَلَى:gen',
        'عَن_أَن':            'عَن:gen',
        'عَن_أَنَّ':            'عَن:gen',
        'عَن_بِ':             'عَن:gen',
        'عَن_فِي_أَن':         'عَن:gen',
        'عَن_مِن':            'عَن:gen',
        'فِي_إِلَى':           'فِي:gen',
        'فِي_أَن':            'فِي:gen',
        'فِي_أَنَّ':            'فِي:gen',
        'فِي_أَنَّ_عَلَى':        'فِي:gen',
        'فِي_أَنَّ_لَدَى':        'فِي:gen',
        'فِي_أَنَّ_مِن':         'فِي:gen',
        'فِي_بِ':             'فِي:gen',
        'فِي_بِ_فِي':          'فِي:gen',
        'فِي_مَا':            'فِي:gen',
        'فِي_مَعَ':            'فِي:gen',
        'فِي_مِن':            'فِي:gen',
        'كَ_لِ':              'كَ:gen',
        'كَ_وَ_وَ':            'كَ:gen',
        'لِ_إِلَى':            'لِ:gen',
        'لِ_أَمَامَ_وَ':         'لِ:gen',
        'لِ_أَن':             'لِ:gen',
        'لِ_عَن':             'لِ:gen',
        'لِ_فِي':             'لِ:gen',
        'لِ_مَعَ':             'لِ:gen',
        'لِ_مِن':             'لِ:gen',
        'لِ_وَ':              'لِ:gen',
        'لِ_وَ_فِي':           'لِ:gen',
        'مَعَ_أَنَّ':            'مَعَ:gen',
        'مَعَ_بِ':             'مَعَ:gen',
        'مِن_إِلَى':           'مِن:gen',
        'مِن_أَن':            'مِن:gen',
        'مِن_أَنَّ':            'مِن:gen',
        'مِن_بِ':             'مِن:gen',
        'مِن_عَلَى':           'مِن:gen',
        'مِن_فِي':            'مِن:gen',
        'مِن_مِن':            'مِن:gen',
        'بِ_مُنَاسَبَة':         'بِمُنَاسَبَةِ:gen', # bimunāsabati = on the occasion of
        'فِي_مَجَال':          'فِي_مَجَالِ:gen', # fī maǧāli = in the area of
        'عَدَا':              'عَدَا:gen', # ʿadā = except for
        'بِ_اِعتِبَار':         'بِاِعتِبَارِ:gen', # bi-iʿtibāri = with regard to
        'بِ_اِعتِبَار_أَنَّ':      'بِاِعتِبَارِ:gen', # bi-iʿtibāri = with regard to
        'بِ_اِعتِبَار_مِن':      'بِاِعتِبَارِ:gen', # bi-iʿtibāri = with regard to
        'بِ_تُهمَة':           'بِتُهمَةِ:gen', # bituhmati = on charges of
        'بِ_فَضل':            'بِفَضلِ:gen', # bifaḍli = thanks to
        'عَلَى_حِسَاب':         'عَلَى_حِسَابِ:gen', # ʿalā ḥisābi = at the expense of
        'لِ_حِسَاب':           'عَلَى_حِسَابِ:gen', # ʿalā ḥisābi = at the expense of
        'عَلَى_رَأس':          'عَلَى_رَأسِ:gen', # ʿalā raʾsi = on top of
        'قُبَيلَ':             'قُبَيلَ:gen', # qubayla = before
        'مَهمَا':             'مَهمَا', # mahmā = regardless
        'مِمَّا':              'مِمَّا', # mimmā = that, which
        'مِمَّا_لَدَى':          'مِمَّا', # mimmā = that, which
        'بِ_اِتِّجَاه':          'بِاِتِّجَاهِ:gen', # bi-ittiǧāhi = towards
        'فِي_اِتِّجَاه':         'بِاِتِّجَاهِ:gen', # bi-ittiǧāhi = towards
        'طَالَمَا':            'طَالَمَا', # ṭālamā = as long as
        'طَالَمَا_أَنَّ':         'طَالَمَا', # ṭālamā = as long as
        'عَلَى_غِرَار':         'عَلَى_غِرَارِ:gen', # ʿalā ġirāri = similar to
        'فَورَ':              'فَورَ:gen', # fawra = as soon as
        'فِي_حَال':           'فِي_حَالِ:gen', # fī ḥāli = in case
        'فِي_حَالَة':          'فِي_حَالِ:gen', # fī ḥāli = in case
        'بِ_حَالَة':           'فِي_حَالِ:gen', # fī ḥāli = in case
        'لِ_مِثلَ':            'مِثلَ', # miṯla = like
        'مِثلَمَا':            'مِثلَ', # miṯla = like
        'مِن_مِثلَ':           'مِثلَ', # miṯla = like
        'بِ_مِثلَ':            'مِثلَ', # miṯla = like
        'فِي_مِثلَ':           'مِثلَ', # miṯla = like
        'إِلَى_مِثلَ':          'مِثلَ', # miṯla = like
        'عَلَى_مِثلَ':          'مِثلَ', # miṯla = like
        'عَن_مِثلَ':           'مِثلَ', # miṯla = like
        'مُنذُ_أَن':           'مُنذُ:gen',
        'مُنذُ_وَ_فِي':         'مُنذُ:gen',
        'إِلَّا':               'إِلَّا', # ʾillā = except, unless
        'إِلَّا_أَنَّ':            'إِلَّا', # ʾillā = except, unless
        'إِلَّا_أَنَّ_هُوَ':         'إِلَّا', # ʾillā = except, unless
        'إِلَّا_أَن':            'إِلَّا', # ʾillā = except, unless
        'إِلَّا_إِذَا':           'إِلَّا', # ʾillā = except, unless
        'عَلَى_إِلَّا':           'إِلَّا', # ʾillā = except, unless
        'بَدَلًا_مِن':           'بَدَلًا_مِن:gen', # badalan min = instead of
        'بِ_حُضُور':           'فِي_حُضُورِ:gen', # together with
        'بِ_صَدَد':            'بِصَدَدِ:gen', # biṣadadi = with respect to
        'بِ_مُقتَضَى':          'بِمُقتَضَى:gen', # bimuqtaḍā = with requirement of
        'خَلفَ':              'خَلفَ:gen', # ḫalfa = behind
        'عَلَى_أَسَاس':         'عَلَى_أَسَاسٍ:gen', # ʿalā ʾasāsin = based on
        'عَلَى_أَسَاس_أَنَّ':      'عَلَى_أَسَاسٍ:gen', # ʿalā ʾasāsin = based on
        'فِي_خِتَام':          'فِي_خِتَامِ', # fī ḫitāmi = in conclusion
        'فِي_ضَوء':           'فِي_ضَوءِ:gen', # fī ḍawʾi = in light of
        'كُلَّمَا':             'كُلَّمَا', # kullamā = whenever
        'لِ_كَون':            'لِكَونِ', # likawni = because
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
                edep['deprel'] = re.sub(r':وَ:', r':', edep['deprel'])
                edep['deprel'] = re.sub(r':وَ$', r'', edep['deprel'])
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
