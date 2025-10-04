"""Block to fix case-enhanced dependency relations in Arabic."""
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
        'أَنَّ':  [],
        'أَن':  [],
        'إِنَّ':  [],
        'إِذَا': [],
        'لَو':  [],
        'حَيثُ': [],
        'مِثلَ': [],
        'لِأَنَّ':  [],
        'كَمَا': [],
#        'فِي_حِينَ': [],
        'فَ':   []
    }

    # Secondary prepositions sometimes have the lemma of the original part of
    # speech. We want the grammaticalized form instead. List even those that
    # will have the same lexical form, as we also want to check the morphological
    # case. And include all other prepositions that have unambiguous morphological
    # case, even if they are not secondary.
    unambiguous = {
        'اِبتِدَاء_مِن':        'مِن:gen',
        'إِثرَ':              'إِثرَ:gen', # ʾiṯra = right after
        'أَثنَاءَ':            'أَثنَاءَ:gen', # ʾaṯnāʾa = during
        'إِذ':               'إِذ', # ʾiḏ = because
        'إِذ_أَنَّ':            'إِذ', # ʾiḏ ʾanna
        'إِذًا':              'إِذَا',
        'إِذَا':              'إِذَا', # remove morphological case; ʾiḏā = if
        'إِزَاءَ':             'إِزَاءَ:gen', # ʾizāʾa = regarding, facing, towards
        'أَلَّا':               'إِلَّا',
        'إِلَّا':               'إِلَّا', # ʾillā = except, unless
        'إِلَّا_إِذَا':           'إِلَّا', # ʾillā = except, unless
        'إِلَّا_أَن':            'إِلَّا', # ʾillā = except, unless
        'إِلَّا_أَنَّ':            'إِلَّا', # ʾillā = except, unless
        'إِلَّا_أَنَّ_هُوَ':         'إِلَّا', # ʾillā = except, unless
        'إِلَى':              'إِلَى:gen', # ʾilā = to
        'إِلَى_أَن':           'إِلَى:gen',
        'إِلَى_أَنَّ':           'إِلَى_أَنَّ', # until? that?
        'إِلَى_أَنَّ_لَدَى':       'إِلَى_أَنَّ',
        'إِلَى_أَنَّ_مِن':        'إِلَى_أَنَّ',
        'إِلَى_أَنَّ_هُوَ':        'إِلَى_أَنَّ',
        'إِلَى_أَنَّ_هُوَ_مِن':     'إِلَى_أَنَّ',
        'إِلَى_أَنَّ_هُوَ_مِن_بَينَ': 'إِلَى_أَنَّ',
        'إِلَى_بَعدَ':          'إِلَى:gen',
        'إِلَى_بَينَ':          'إِلَى_بَينِ:gen', # ʾilā bayni = to between
        'إِلَى_جَانِب':         'إِلَى_جَانِبِ:gen', # ʾilā ǧānibi = beside
        'إِلَى_حَوَالَى':        'إِلَى:gen', # ila hawala = to around X
        'إِلَى_حَوَالَى_مِن':     'إِلَى:gen', # ila hawala min
        'إِلَى_حَيثُ':          'إِلَى:gen',
        'إِلَى_حِينَ':          'فِي_حِينِ', # during
        'إِلَى_خَارِجَ':         'إِلَى_خَارِجِ:gen', # ʾilā ḫāriǧi = out
        'إِلَى_فِي':           'إِلَى:gen',
        'إِلَى_قَبلَ':          'إِلَى_قَبلِ:gen', # ʾilā qabli = until before X (e.g. until one year ago)
        'إِلَى_مِثلَ':          'مِثلَ', # miṯla = like
        'إِلَى_نَحوَ':          'إِلَى:gen', # to about N
        'أَمَّا':              'أَمَامَ:gen',
        'إِمَّا_لِ':            'لِ:gen',
        'أَمَامَ':             'أَمَامَ:gen', # ʾamāma = in front of
        'أَمَامَ_مِن':          'أَمَامَ:gen',
        'أَن':               'أَنَّ', # remove morphological case; ʾanna = that
        'أَنَّ':               'أَنَّ', # remove morphological case; ʾanna = that
        'إِن':               'إِنَّ', # remove morphological case; ʾinna = that
        'إِنَّ':               'إِنَّ', # remove morphological case; ʾinna = that
        'إِنَّمَا':             'إِنَّ',
        'إِيَّا':              'إِلَّا',
        'بِ':                'بِ:gen', # bi = for, with
        'بِ_اِتِّجَاه':          'بِاِتِّجَاهِ:gen', # bi-ittiǧāhi = towards
        'بِ_إِزَاءَ':           'إِزَاءَ:gen', # ʾizāʾa = regarding, facing, towards
        'بِ_اِستِثنَاء':        'بِاِستِثنَاءِ:gen', # biistiṯnāʾi = with exception of
        'بِ_اِسم':            'بِاِسمِ:gen', # biismi = in name of
        'بِ_إِضَافَة_إِلَى':      'بِاَلإِضَافَةِ_إِلَى:gen', # bi-al-ʾiḍāfati ʾilā = in addition to
        'بِ_إِضَافَة_إِلَى_أَنَّ':   'إِلَى_أَنَّ',
        'بِ_إِضَافَة_لِ':        'بِاَلإِضَافَةِ_إِلَى:gen', # in addition to
        'بِ_اِعتِبَار':         'بِاِعتِبَارِ:gen', # bi-iʿtibāri = with regard to
        'بِ_اِعتِبَار_أَنَّ':      'بِاِعتِبَارِ:gen', # bi-iʿtibāri = with regard to
        'بِ_اِعتِبَار_مِن':      'بِاِعتِبَارِ:gen', # bi-iʿtibāri = with regard to
        'بِ_اِعتِمَاد_عَلَى':     'بِاَلِاعتِمَادِ_عَلَى:gen', # bi-al-i-ʼʿtimādi ʿalā = depending on
        'بِ_إِلَى':            'بِ:gen',
        'بِ_أَنَّ':             'أَنَّ', # that
        'بِ_أَن':             'بِ:gen',
        'بِ_إِنَّ':             'بِ:gen',
        'بِ_أَنَّ_أَمَامَ':        'أَنَّ', # that
        'بِ_أَنَّ_لَا':           'أَنَّ', # that
        'بِ_أَنَّ_مِن':          'أَنَّ', # that
        'بِ_أَنَّ_هما_مِن':      'أَنَّ', # that
        'بِ_أَنَّ_هُوَ':          'أَنَّ', # that
        'بِ_أَنَّ_هُوَ_عَلَى':      'أَنَّ', # that
        'بِ_اِنطِلَاق':          'بِ:gen',
        'بِ_تَالِي_إِنَّ':        'بِ:gen',
        'بِ_تَعَاوُن_مَعَ':       'بِاَلتَّعَاوُنِ_مَعَ:gen', # bi-at-taʿāwuni maʿa = in cooperation with
        'بِ_تُهمَة':           'بِتُهمَةِ:gen', # bituhmati = on charges of
        'بِ_تَوَازِي_مَعَ':       'بِاَلتَّوَازِي_مَعَ:gen', # bi-at-tawāzī maʿa = in parallel with
        'بِ_ثُمَّ':             'بِ:gen',
        'بِ_جَانِب':           'بِجَانِبِ:gen', # biǧānibi = next to
        'بِ_جِهَة':            'بِ:gen',
        'بِ_حَالَة':           'فِي_حَالِ:gen', # fī ḥāli = in case
        'بِ_حَسَبَ':            'حَسَبَ:gen', # ḥasaba = according to, depending on
        'بِ_حُضُور':           'فِي_حُضُورِ:gen', # together with
        'بِ_حَقّ':             'بِ:gen',
        'بِ_حُكم':            'بِ:gen',
        'بِ_حُلُول':           'بِ:gen',
        'بِ_حَوَالَى':          'بِ:gen', # bi hawala = with around X
        'بِ_حَيثُ':            'بِ:gen',
        'بِ_خُصُوص':           'بِخُصُوصِ:gen', # biḫuṣūṣi = with regard
        'بِ_خِلَاف':            'بِخِلَافِ:gen', # biḫilāfi = in addition to
        'بِ_دَاخِلَ':           'دَاخِلَ:gen',
        'بِ_دَعوَى':           'بِ:gen',
        'بِ_دَور':            'بِ:gen', # bidawri = with role, in turn?
        'بِ_دُون':            'دُونَ:gen',
        'بِ_دُونَ':            'دُونَ:gen', # bi dūni = without
        'بِ_دُونَ_أَن':         'دُونَ:gen', # bi dūni ʾan = without
        'بِ_رِعَايَة':          'بِ:gen',
        'بِ_رَغم':            'رَغمَ:gen', # despite
        'بِ_رَغم_أَنَّ':         'رَغمَ:gen', # despite
        'بِ_رَغم_مِن':         'رَغمَ:gen', # despite
        'بِ_رَغم_مِن_أَن':      'بِ:gen',
        'بِ_رَغم_مِن_أَنَّ':      'رَغمَ:gen', # despite
        'بِ_رَغم_مِن_أَنَّ_هُوَ':   'بِ:gen',
        'بِ_رِفقَة':           'بِرِفقَةٍ:gen', # birifqatin = in company of
        'بِ_رِئَاسَة':          'بِ:gen',
        'بِ_سَبّ':             'بِ:gen',
        'بِ_سَبَب':            'بِسَبَبِ:gen', # bisababi = because of
        'بِ_شَأن':            'بِشَأنِ:gen', # bišaʾni = about, regarding (lit. with + matter)
        'بِ_شَرط_أَن':         'بِ:gen',
        'بِ_صَدَد':            'بِصَدَدِ:gen', # biṣadadi = with respect to
        'بِ_صَرف_نَظَر_عَن':     'بِصَرفِ_اَلنَّظَرِ_عَن:gen', # biṣarfi an-naẓari ʿan = regardless of
        'بِ_صِفَة':            'بِصِفَةِ:gen', # biṣifati = as
        'بِ_صُورَة':            'بِ:gen',
        'بِ_عَكس':            'بِ:gen',
        'بِ_عَلَى':            'بِ:gen',
        'بِ_عَن':             'بِ:gen',
        'بِ_عَين':            'بِ:gen',
        'بِ_غَضّ_نَظَر_عَن':      'بِغَضِّ_اَلنَّظَرِ_عَن:gen', # biġaḍḍi an-naẓari ʿan = regardless of
        'بِ_فَضل':            'بِفَضلِ:gen', # bifaḍli = thanks to
        'بِ_فِي':             'بِ:gen',
        'بِ_قَدر':            'بِ:gen',
        'بِ_قُرب_مِن':         'بِاَلقُربِ_مِن:gen', # bi-al-qurbi min = near (with proximity to)
        'بِ_قَصد':            'بِقَصدِ:gen', # biqaṣdi = with intention
        'بِ_كَ':              'بِ:gen',
        'بِ_لِ':              'بِ:gen',
        'بِ_لَا':              'بِ:gen',
        'بِ_مَا_أَنَّ':          'بِ:gen',
        'بِ_مَثَابَة':          'بِ:gen',
        'بِ_مِثلَ':            'مِثلَ', # miṯla = like
        'بِ_مُجَرَّد':           'بِ:gen',
        'بِ_مُسَاعَدَة':         'بِ:gen',
        'بِ_مُشَارَكَة':         'بِمُشَارَكَةِ:gen', # bimušārakati = with participation of
        'بِ_مُقَارَنَة_بِ':       'بِاَلمُقَارَنَةِ_بِ:gen', # bi-al-muqāranati bi = in comparison to
        'بِ_مُقتَضَى':          'بِمُقتَضَى:gen', # bimuqtaḍā = with requirement of
        'بِ_مِقدَار':          'بِ:gen',
        'بِ_مِن':             'بِ:gen',
        'بِ_مُنَاسَبَة':         'بِمُنَاسَبَةِ:gen', # bimunāsabati = on the occasion of
        'بِ_مُوجِب':           'بِمُوجِبِ:gen', # bimūǧibi = with motive
        'بِ_نَتِيجَة':          'بِ:gen',
        'بِ_نَحوَ':            'بِ:gen', # by about N
        'بِ_نِسبَة':           'بِاَلنِّسبَةِ_لِ:gen', # bi an-nisbati (bin-nisbati) = in proportion/relation to
        'بِ_نِسبَة_إِلَى':       'بِاَلنِّسبَةِ_لِ:gen', # bi an-nisbati ʾilā (bin-nisbati ʾilā) = in proportion/relation to
        'بِ_نِسبَة_لِ':         'بِاَلنِّسبَةِ_لِ:gen', # bi an-nisbati li (bin-nisbati li) = in proportion/relation to
        'بِ_نِسبَة_لِ_مِن':      'بِاَلنِّسبَةِ_لِ:gen', # bi an-nisbati li (bin-nisbati li) = in proportion/relation to
        'بِ_نَظَر_إِلَى':        'بِ:gen',
        'بِ_نِيَابَة_عَن':       'بِاَلنِّيَابَةِ_عَن:gen', # bi-an-niyābati ʿan = on behalf of
        'بِ_هَدَف':            'بِهَدَفِ:gen', # bihadafi = with goal
        'بِ_وَ_لِ':            'بِ:gen',
        'بِ_وَاسِطَة':          'بِوَاسِطَةِ:gen', # biwāsiṭati = by means of
        'بِ_وَاقِع':           'بِ:gen',
        'بِ_وَسَط':            'بِوَسَطِ:gen', # biwasaṭi = in the middle of
        'بِ_وَسطَ':            'وَسطَ:gen', # wasṭa = in the middle
        'بِ_وَصف':            'بِ:gen',
        'بازاء':            'بِ:gen',
        'بالتسخين':         'بِ:gen',
        'بَدَلًا_مِن':           'بَدَلًا_مِن:gen', # badalan min = instead of
        'بدون':             'دُونَ:gen', # without
        'بشان':             'بِشَأنِ:gen',
        'بَعدَ':              'بَعدَ:gen', # baʿda = after
        'بَعدَ_أَن':           'بَعدَ:gen', # baʿda ʾan = after + clause
        'بَعدَ_حَوَالَى':        'بَعدَ:gen', # baada hawala
        'بَعدَ_نَحوَ':          'بَعدَ:gen', # after about N
        'بَعدَمَا':            'بَعدَ:gen', # baʿdamā = after
        'بُعَيدَ':             'بُعَيدَ:gen', # buʿayda = shortly after
        'بَل':               'قَبلَ:gen',
        'بِنَاء_عَلَى':         'بناء_عَلَى:gen',
        'بناء_عَلَى':         'بناء_عَلَى:gen', # bnāʾ ʿalā = based on
        'بناء_لِ':           'لِ:gen',
        'بَيدَ':              'بِ:gen',
        'بَيدَ_أَنَّ':           'بِ:gen',
        'بَينَ':              'بَينَ:gen', # bayna = between
        'بَينَ_حَوَالَى':        'بَينَ:gen', # bayna hawala
        'بينا':             'بَينَ:gen', # bayna = between
        'بَينَ_وَ_وَ_وَ':             'بَينَ:gen', # bayna = between
        'بَينَمَا':            'بَينَ:gen',
        'بَينَمَا_لَم':         'بَينَ:gen',
        'تُجَاهَ':             'تُجَاهَ:gen', # tuǧāha = towards, facing
        'تَحتَ':              'تَحتَ:gen', # tahta = under
        'ثَمَّ':               'بِ:gen',
        'ثُمَّ':               'بِ:gen',
        'جَرَّاء':             'جَرَّاء:gen', # ǧarrāʾ = because of
        'حَتَّى':              'حَتَّى:gen', # ḥattā = until
        'حَتَّى_أَنَّ':           'حَتَّى:gen', # before
        'حَتَّى_إِنَّ':           'حَتَّى:gen', # before
        'حَتَّى_بِ':            'حَتَّى:gen', # before
        'حَتَّى_لَو':           'لَو', # even if
        'حَتَّى_وَ_لَو':         'لَو', # even if
        'حَتَّى_وإن':          'إِنَّ',
        'حَسَبَ':              'حَسَبَ:gen', # ḥasaba = according to, depending on
        'حَسَبَمَا':            'حَسَبَ:gen', # ḥasaba = according to, depending on
        'حَوَالَى':            'حَوَالَى', # ḥawālā = around, about
        'حَوَالَى_مِن':         'مِن:gen', # hawala min = from around X
        'حَولَ':              'حَولَ:gen', # ḥawla = about
        'حولما_إِذَا':        'إِذَا',
        'حِيَالَ':             'حِيَالَ:gen', # ḥiyāla = concerning
        'حَيثُ':              'حَيثُ', # remove morphological case; ḥayṯu = where (SCONJ, not ADV)
        'حِينَمَا':            'فِي_حِينِ', # during
        'خَارِجَ':             'خَارِجَ:gen', # ḫāriǧa = outside
        'خِلَالَ':              'خِلَالَ:gen', # ḫilāla = during
        'خَلفَ':              'خَلفَ:gen', # ḫalfa = behind
        'دَاخِل':
                    'دَاخِلَ:gen', # dāḫila = inside of
        'دَاخِلَ':
                    'دَاخِلَ:gen', # dāḫila = inside of
        'دُونَ':              'دُونَ:gen', # dūna = without
        'دُونَ_أَن':           'دُونَ:gen', # dūna ʾan = without
        'دُونَ_سِوَى':          'دُونَ:gen', # dūna siwā = without
        'دونما':            'دُونَ:gen',
        'ذٰلِكَ_بَعدَمَا':        'بَعدَ:gen',
        'ذٰلِكَ_عِندَمَا':        'بِ:gen',
        'ذٰلِكَ_لِأَنَّ':           'لِأَنَّ', # because
        'ذٰلِكَ_لِكَي':          'لِكَي', # li-kay = in order to
        'ذٰلِكَ_نَظَر_لِ':        'بِ:gen',
        'رَغمَ':              'رَغمَ:gen', # raġma = despite
        'رَغمَ_أَنَّ':           'رَغمَ:gen', # raġma ʾanna = despite + clause
        'رَغمَ_أَنَّ_مِن':        'رَغمَ:gen', # raġma ʾanna min = despite
        'رَهنَ':              'رَهنَ:gen', # rahna = depending on
        'رَيثَمَا':            'رَهنَ:gen', # rahna = depending on
        'سِوَى':              'سِوَى:gen', # siwā = except for
        'سِوَى_أَنَّ_هُوَ':        'سِوَى:gen', # siwā = except for
        'سِوَى_بِ':            'سِوَى:gen', # siwā = except for
        'سِوَى_عَلَى':          'سِوَى:gen', # siwā = except for
        'سِوَى_لِ':            'سِوَى:gen', # siwā = except for
        'ضِدَّ':               'ضِدَّ:gen', # ḍidda = against
        'ضِمنَ':              'ضِمنَ:gen', # ḍimna = within, inside, among
        'طَالَمَا':
                    'طَالَمَا', # ṭālamā = as long as
        'طالَما':
                    'طَالَمَا', # ṭālamā = as long as
        'طَالَمَا_أَنَّ':
                    'طَالَمَا', # ṭālamā = as long as
        'طِوَالَ':             'طِوَالَ:gen', # ṭiwāla = throughout
        'طِيلَةَ':             'طِيلَةَ:gen', # ṭīlata = during
        'عبر':              'عَبرَ:gen',
        'عَبرَ':              'عَبرَ:gen', # ʿabra = via
        'عَدَا':              'عَدَا:gen', # ʿadā = except for
        'عَقِبَ':              'عَقِبَ:gen', # ʿaqiba = following
        'عَقِبَ_أَن':           'عَقِبَ:gen', # ʿaqiba = following
        'عَقِبَ_مِن':           'عَقِبَ:gen', # ʿaqiba = following
        'عَلَى':              'عَلَى:gen', # ʿalā = on
        'عَلَى_أبواب':        'عَلَى:gen',
        'عَلَى_إِثرَ':          'إِثرَ:gen', # ʿalā ʾiṯri = right after
        'عَلَى_أَثَر':          'عَلَى:gen',
        'عَلَى_اِختِلَاف':        'عَلَى:gen',
        'عَلَى_أَسَاس':         'عَلَى_أَسَاسٍ:gen', # ʿalā ʾasāsin = based on
        'عَلَى_أَسَاس_أَنَّ':      'عَلَى_أَسَاسٍ:gen', # ʿalā ʾasāsin = based on
        'عَلَى_اِعتِبَار_أَنَّ':    'عَلَى_اِعتِبَارِ_أَنَّ', # ʿalā iʿtibāri ʾanna = considering that
        'عَلَى_إِلَّا':           'إِلَّا', # ʾillā = except, unless
        'عَلَى_الفور':
                       'عَلَى:gen', # ʿalā = on
        'عَلَى_إِلَى':
                       'عَلَى:gen', # ʿalā = on
        'عَلَى_أَن':
                       'عَلَى:gen', # ʿalā = on
        'عَلَى_أَنَّ':
                       'عَلَى:gen', # ʿalā = on
        'عَلَى_أَن_بِ':
                       'عَلَى:gen', # ʿalā = on
        'عَلَى_أَنَّ_عَلَى':
                       'عَلَى:gen', # ʿalā = on
        'عَلَى_أَنَّ_مِن_شَأن':
                       'عَلَى:gen', # ʿalā = on
        'عَلَى_أَنَّ_هُوَ':
                       'عَلَى:gen', # ʿalā = on
        'عَلَى_أَنَّ_هُوَ_لَدَى':
                       'عَلَى:gen', # ʿalā = on
        'عَلَى_بِ':
                       'عَلَى:gen', # ʿalā = on
        'عَلَى_بِ_فِي':
                       'عَلَى:gen', # ʿalā = on
        'عَلَى_بَينَ':
                       'عَلَى:gen', # ʿalā = on
        'عَلَى_حَدّ':
                       'عَلَى:gen', # ʿalā = on
        'عَلَى_حِسَاب':         'عَلَى_حِسَابِ:gen', # ʿalā ḥisābi = at the expense of
        'عَلَى_حَسَبَ':          'حَسَبَ:gen', # ḥasaba = according to, depending on
        'عَلَى_حَولَ':          'عَلَى:gen',
        'عَلَى_رَأس':          'عَلَى_رَأسِ:gen', # ʿalā raʾsi = on top of
        'عَلَى_رَغم':          'عَلَى_رَغمِ:gen', # ʿalā raġmi = despite
        'عَلَى_رَغمَ_أَنَّ':       'رَغمَ:gen', # ʿalā raġma ʾanna = despite + clause
        'عَلَى_رَغم_أَنَّ':       'عَلَى_رَغمِ:gen', # ʿalā raġmi = despite
        'عَلَى_رَغم_مِن':       'عَلَى_رَغمِ:gen', # ʿalā raġmi = despite
        'عَلَى_رَغم_مِن_أَنَّ':    'عَلَى_رَغمِ:gen', # ʿalā raġmi = despite
        'عَلَى_رَغم_مِن_أَنَّ_هُوَ': 'عَلَى_رَغمِ:gen', # ʿalā raġmi = despite
        'عَلَى_طَرِيقَة':        'عَلَى_طَرِيقَةِ:gen', # ʿalā ṭarīqati = on the way
        'عَلَى_عَكس':          'عَلَى:gen',
        'عَلَى_غِرَار':         'عَلَى_غِرَارِ:gen', # ʿalā ġirāri = similar to
        'عَلَى_قَيد':          'عَلَى:gen',
        'عَلَى_لِسَان':         'عَلَى:gen',
        'عَلَى_مِثلَ':          'مِثلَ', # miṯla = like
        'عَلَى_مدى':          'عَلَى:gen',
        'عَلَى_مَدَى':          'عَلَى_مَدَى:gen', # ʿalā madā = on period
        'عَلَى_مَقرَبَة_مِن':     'عَلَى_مَقرَبَةٍ_مِن:gen', # ʿalā maqrabatin min = in the vicinity of
        'عَلَى_مِن':           'عَلَى:gen',
        'عَلَى_نَحوَ':          'عَلَى:gen', # to about N
        'عَلَى_يَد':           'عَلَى:gen',
        'عَن':               'عَن:gen', # ʿan = about, from
        'عَن_أَن':            'عَن:gen',
        'عَن_أَنَّ':            'عَن:gen',
        'عَن_أَنَّ_وَرَاءَ':       'وَرَاءَ:gen', # warāʾa = behind, past, beyond
        'عَن_بِ':             'عَن:gen',
        'عَن_طَرِيق':          'عَن_طَرِيقِ:gen', # ʿan ṭarīqi = via
        'عَن_فِي_أَن':         'عَن:gen',
        'عَن_قُربَ':           'قُربَ:gen', # qurba = near
        'عَن_مِثلَ':           'مِثلَ', # miṯla = like
        'عَن_مِن':            'عَن:gen',
        'عِندَ':              'عِندَمَا', # ʿinda = when
        'عِندَمَا':            'عِندَمَا', # ʿindamā = when
        'غَيرَ':              'إِلَّا',
        'فَ':                'فَ', # fa = so (advcl or coordination)
        'فَ_إِذَا':            'فَ', # fa = so (advcl or coordination)
        'فَ_بَدَل_مِن_أَن':      'فَ', # fa = so (advcl or coordination)
        'فَ_بَينَ':            'فَ', # fa = so (advcl or coordination)
        'فَ_عَلَى':            'فَ', # fa = so (advcl or coordination)
        'فَ_فِي':             'فَ', # fa = so (advcl or coordination)
        'فَ_مِن':             'فَ', # fa = so (advcl or coordination)
        'فَورَ':              'فَورَ:gen', # fawra = as soon as
        'فَوقَ':              'فَوقَ:gen', # fawqa = above, over
        'فِي':               'فِي:gen', # fī = in
        'فِي_اِتِّجَاه':         'بِاِتِّجَاهِ:gen', # bi-ittiǧāhi = towards
        'فِي_أَثنَاءَ':         'أَثنَاءَ:gen', # ʾaṯnāʾa = during
        'فِي_إِطَار':          'فِي_إِطَار:gen', # fī ʾiṭār = in frame
        'فِي_اعقاب':         'فِي_أَعقَابِ:gen',
        'فِي_إِلَى':           'فِي:gen',
        'فِي_أَن':            'فِي:gen',
        'فِي_أَنَّ':            'فِي:gen',
        'فِي_أَنَّ_عَلَى':        'فِي:gen',
        'فِي_أَنَّ_لَدَى':        'فِي:gen',
        'فِي_أَنَّ_مِن':         'فِي:gen',
        'فِي_بِ':             'فِي:gen',
        'فِي_بِ_فِي':          'فِي:gen',
        'فِي_بَاطِن':          'فِي:gen',
        'فِي_بَعدَ':           'فِي:gen',
        'فِي_بَينَ':           'بَينَ:gen',
        'فِي_حَال':           'فِي_حَالِ:gen', # fī ḥāli = in case
        'فِي_حَالَة':          'فِي_حَالِ:gen', # fī ḥāli = in case
        'فِي_حَدّ':            'فِي:gen',
        'فِي_حُضُور':          'فِي_حُضُورِ:gen', # fī ḥuḍūri = in presence of
        'فِي_حَقّ':            'فِي:gen',
        'فِي_حُكم':           'فِي:gen',
        'فِي_حَوَالَى':         'فِي:gen', # fi hawala = in around X
        'فِي_حِين':
                    'فِي_حِينِ', # fī ḥīni = while
        'فِي_حِينَ':
                    'فِي_حِينِ', # fī ḥīni = while
        'فِي_حِين_أَنَّ':
                    'فِي_حِينِ', # fī ḥīni = while
        'فِي_حِينَ_أَنَّ_هُوَ':
                    'فِي_حِينِ', # fī ḥīni = while
        'فِي_خَارِجَ':          'خَارِجَ:gen', # ḫāriǧa = outside
        'فِي_خِتَام':          'فِي_خِتَامِ:gen', # fī ḫitāmi = in conclusion
        'فِي_خِتَامِ':          'فِي_خِتَامِ:gen', # fī ḫitāmi = in conclusion
        'فِي_خِلَالَ':           'فِي:gen',
        'فِي_دَاخِل':
                      'دَاخِلَ:gen',
        'فِي_دَاخِلَ':          'فِي:gen',
        'فِي_سَبِيل':          'فِي_سَبِيلِ:gen', # fī sabīli = in order to
        'فِي_سِيَاق':          'فِي:gen',
        'فِي_شَأن':           'فِي_شَأنِ:gen', # fī šaʾni = in regard of
        'فِي_شَكل':           'فِي:gen',
        'فِي_صَفّ':            'فِي:gen',
        'فِي_صُورَة':          'فِي:gen',
        'فِي_ضَوء':           'فِي_ضَوءِ:gen', # fī ḍawʾi = in light of
        'فِي_ظِلّ':            'فِي_ظِلِّ:gen', # fī ẓilli = in light of
        'فِي_عُقب':           'فِي_أَعقَابِ:gen', # fī ʾaʿqābi = in the aftermath of
        'فِي_غَضن':           'فِي:gen',
        'فِي_غُضُون':          'فِي:gen',
        'فِي_مَا':            'فِي:gen',
        'فِي_مِثلَ':           'مِثلَ', # miṯla = like
        'فِي_مَجَال':          'فِي_مَجَالِ:gen', # fī maǧāli = in the area of
        'فِي_مستشفى':        'فِي:gen',
        'فِي_مَعَ':            'فِي:gen',
        'فِي_مُقَابِلَ':         'مُقَابِلَ:gen',
        'فِي_مَقدَم':          'فِي:gen',
        'فِي_مِن':            'فِي:gen',
        'فِي_مُنَاسَبَة':        'فِي_مُنَاسَبَةِ:gen', # fī munāsabati = on the occasion of
        'فِي_مُوَاجَهَة':        'فِي:gen',
        'فِي_نَحوَ':           'فِي:gen', # in about N
        'فِي_نِطَاق':          'فِي:gen',
        'فِي_وَجه':           'فِي:gen',
        'فِي_وَسط':           'وَسطَ:gen',
        'فِي_وَسطَ':           'وَسطَ:gen', # wasṭa = in the middle
        'فِيمَا':             'فِيمَا', # fīmā = while
        'قُبَالَةَ':            'قُبَالَةَ:gen', # qubālata = in front of, facing
        'قَبلَ':              'قَبلَ:gen', # qabla = before
        'قَبلَ_أَن':           'قَبلَ:gen', # qabla = before
        'قَبلَ_حَوَالَى':        'قَبلَ:gen', # qabla hawala
        'قَبلَ_نَحوَ':          'قَبلَ:gen', # before about N
        'قُبَيلَ':             'قُبَيلَ:gen', # qubayla = before
        'قُربَ':              'قُربَ:gen', # qurba = near
        'قَيدَ':              'فِي:gen',
        'كَ':                'كَ:gen', # ka = in (temporal?)
        'كَ_أَنَّ':             'كَ:gen',
        'كَ_لِ':              'كَ:gen',
        'كَ_وَ_وَ':            'كَ:gen',
        'كَأَنَّمَا':            'كَأَنَّمَا', # ka-ʾannamā = as if
        'كُلَّمَا':             'كُلَّمَا', # kullamā = whenever
        'كَمَا':              'كَمَا', # remove morphological case; kamā = as
        'كَي':               'لِكَي', # kay = in order to
        'لَ':                'لِ:gen',
        'لَ_عَلَّ':                'لِ:gen',
        'لِ':                'لِ:gen', # li = to
        'لِ_أَجَلّ':            'لِ:gen',
        'لِ_إِلَى':            'لِ:gen',
        'لِ_أَمَامَ_وَ':         'لِ:gen',
        'لِ_أَن':             'لِ:gen',
        'لِ_بِ':              'لِ:gen',
        'لِ_جِهَة':            'لِ:gen',
        'لِ_حِسَاب':           'عَلَى_حِسَابِ:gen', # ʿalā ḥisābi = at the expense of
        'لِ_حَوَالَى':          'لِ:gen', # li hawala = for around X
        'لِ_خَارِجَ':           'لِخَارِجِ:gen', # liḫāriǧi = out
        'لِ_دُخُول':           'لِ:gen',
        'لِ_دَرَجَة_أَنَّ':        'لِ:gen',
        'لِ_سَبَب':            'لِ:gen',
        'لِ_صَالِح':           'لِصَالِحِ:gen', # liṣāliḥi = in interest of
        'لِ_عَلَى':            'لِ:gen',
        'لِ_عَن':             'لِ:gen',
        'لِ_عِندَ':            'لِ:gen',
        'لِ_فِي':             'لِ:gen',
        'لِ_فِي_بَينَ':         'لِ:gen',
        'لِ_كَون':            'لِكَونِ', # likawni = because
        'لِ_لِئَلّا':            'لِ:gen',
        'لِ_مِثلَ':            'مِثلَ', # miṯla = like
        'لِ_مَعَ':             'لِ:gen',
        'لِ_مِن':             'لِ:gen',
        'لِ_نَحوَ':            'لِ:gen', # to/for about N
        'لِ_وَ':              'لِ:gen',
        'لِ_وَ_فِي':           'لِ:gen',
        'لَا':                'إِلَّا',
        'لَا_سِيَّمَا_بَعدَ':       'بَعدَ:gen',
        'لَا_سِيَّمَا_وَ_أَنَّ':      'أَنَّ',
        'لَا_سِيَّمَا_وَ_أَنَّ_هُوَ':   'أَنَّ',
        'لِأَنَّ':               'لِأَنَّ', # remove morphological case; li-ʾanna = because
        'لدى':              'لَدَى:gen',
        'لَدَى':              'لَدَى:gen', # ladā = with, by, of, for
        'لِذَا':              'لِذَا', # liḏā = so, therefore
        'لِذَا_فَ':            'لِ:gen',
        'لِذٰلِكَ':             'لِذَا', # liḏā = so, therefore
        'لٰكِنَّ':              'مَعَ:gen',
        'لكن_إِذَا':          'إِذَا',
        'لكن_بِ':            'بِ:gen',
        'لٰكِن_بَعدَ':          'بَعدَ:gen',
        'لكن_دَاخِلَ':         'دَاخِلَ:gen',
        'لكن_لَدَى':          'لَدَى:gen',
        'لٰكِن_مَعَ':           'مَعَ:gen',
        'لِكَي':              'لِكَي', # li-kay = in order to
        'لَمَّا':              'كُلَّمَا',
        'لَمَّا_لِ':            'كُلَّمَا',
        'لَو':               'لَو', # law = if
        'لَو_أَنَّ':            'لَو', # if
        'لَو_مِن':            'لَو', # if
        'ما':               'مِمَّا',
        'مَا':               'مِمَّا',
        'ما_دَام':           'مِمَّا',
        'مادامت':           'مِمَّا',
        'مَالَم':             'مَالَم', # mālam = unless
        'مِثلَ':              'مِثلَ', # remove morphological case; miṯla = like
        'مِثلَمَا':            'مِثلَ', # miṯla = like
        'مَعَ':               'مَعَ:gen', # maʿa = with
        'مَعَ_أَنَّ':            'مَعَ:gen',
        'مَعَ_بِ':             'مَعَ:gen',
        'مَعَ_فِي':            'مَعَ:gen',
        'مَعَ_مِن_بَينَ':        'بَينَ:gen',
        'مقابل':            'مُقَابِلَ:gen',
        'مُقَابِلَ':            'مُقَابِلَ:gen', # muqābila = in exchange for, opposite to, corresponding to
        'مُقَابِلَ_حَوَالَى':      'مُقَابِلَ:gen', # muqabila hawala
        'مُقَارَن_بِ':          'بِ:gen',
        'مِمَّا':              'مِمَّا', # mimmā = that, which
        'مِمَّا_لَدَى':          'مِمَّا', # mimmā = that, which
        'مِن':               'مِن:gen', # min = from
        'مِن_اجل':           'مِن_أَجلِ:gen', # min ʾaǧli = for the sake of
        'مِن_أَجل':           'مِن_أَجلِ:gen', # min ʾaǧli = for the sake of
        'مِن_أَجل_أَن':        'مِن:gen',
        'مِن_إِلَى':           'مِن:gen',
        'مِن_أَن':            'مِن:gen',
        'مِن_أَنَّ':            'مِن:gen',
        'مِن_بِ':             'مِن:gen',
        'مِن_بَعدَ':           'مِن:gen',
        'مِن_بَينَ':           'بَينَ:gen',
        'مِن_تَحتَ':           'مِن:gen',
        'مِن_ثَمَّ':            'مِن:gen',
        'مِن_ثُمَّ':            'مِن:gen',
        'مِن_جَانِب':          'إِلَى_جَانِبِ:gen', # min ǧānibi = beside
        'مِن_جَرَّاء':          'جَرَّاء:gen', # ǧarrāʾ = because of
        'مِن_حَوَالَى':         'مِن:gen', # min hawala = from around X
        'مِن_حَولَ':           'مِن:gen',
        'مِن_حَيثُ':           'مِن:gen',
        'مِن_خَارِج':          'مِن_خَارِجِ:gen', # min ḫāriǧi = from outside
        'مِن_خَارِجَ':          'مِن_خَارِجِ:gen', # min ḫāriǧi = from outside
        'مِن_خِلَالَ':           'مِن_خِلَالِ:gen', # min ḫilāli = through, during
        'مِن_دَاخِلَ':          'مِن_دَاخِلِ:gen', # min dāḫili = from inside
        'مِن_دُون':           'مِن_دُونِ:gen', # min dūni = without, beneath, underneath
        'مِن_دُونَ':           'مِن_دُونِ:gen', # min dūni = without, beneath, underneath
        'مِن_دُون_أَن':        'مِن_دُونِ:gen',
        'مِن_دُونَ_أَن':        'مِن_دُونِ:gen', # min dūni ʾan = without, beneath, underneath + clause
        'مِن_زَاوِيَة':         'مِن:gen',
        'مِن_شَأن':           'مِن_شَأنِ:gen', # min šaʾni = from matter
        'مِن_ضِمنَ':           'مِن_ضِمنِ:gen', # min ḍimni = from within = including
        'مِن_طَرَف':           'مِن:gen',
        'مِن_عَلَى':           'مِن:gen',
        'مِن_عِندَ':           'مِن:gen',
        'مِن_غَير_أَن':        'مِن:gen',
        'مِن_فَوقَ':           'مِن_فَوقِ:gen', # min fawqi = from above
        'مِن_فِي':            'مِن:gen',
        'مِن_قَبلَ':           'مِن_قِبَلِ:gen',
        'مِن_قِبَل':           'مِن_قِبَلِ:gen', # min qibali = by
        'مِن_قِبَل_بِ_فِي':      'مِن_قِبَلِ:gen', # min qibali = by
        'مِن_مِثلَ':           'مِثلَ', # miṯla = like
        'مِن_مِن':            'مِن:gen',
        'مِن_مِن_بَينَ':        'بَينَ:gen',
        'مِن_مَوقِع':          'مِن:gen',
        'مِن_نَاحِيَة':         'مِن:gen',
        'مِن_وَرَاءَ':          'مِن_وَرَاءِ:gen', # min warāʾi = from behind
        'مُنذُ':              'مُنذُ:gen', # munḏu = since
        'مُنذُ_أَن':           'مُنذُ:gen',
        'مُنذُ_نَحوَ':          'مُنذُ:gen', # since about N
        'مُنذُ_وَ_فِي':         'مُنذُ:gen',
        'مَهمَا':             'مَهمَا', # mahmā = regardless
        'نَاهِيك_بِ':          'بِ:gen',
        'نَتِيجَة_لِ':          'لِ:gen',
        'نَحوَ':              'نَحوَ', # naḥwa = about, approximately
        'نَحوَ_بِ':            'بِ:gen', # about by N
        'هذا_بالأضافة':      'بِ:gen',
        'وان':              'أَنَّ',
        'وإن':              'إِنَّ',
        'وبشان':            'بِشَأنِ:gen',
        'وَرَاءَ':             'وَرَاءَ:gen', # warāʾa = behind, past, beyond
        'وَسطَ':              'وَسطَ:gen', # wasṭa = in the middle
        'وِفقَ':              'وِفقَ:gen', # wifqa = according to
        'وِفق_لِ':            'وِفقَ:gen', # wifqa = according to
        'ولو':              'إِذَا', # walaw = even if
        'ولو_أَنَّ':           'إِذَا' # walaw = even if
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
        assert(bdeprel[-1] != ':')
        edeprel = bdeprel
        if cdeprel:
            assert(cdeprel[0] != ':')
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
                if edep['deprel'] == 'advcl:pred:إِذَن' or edep['deprel'] == 'advcl:pred:كدا' or edep['deprel'] == 'advcl:pred:لكن':
                    edep['deprel'] = 'advcl:pred'
                    continue
                if edep['deprel'] == 'nmod:بِأَسْرِ:gen':
                    edep['deprel'] = 'nmod'
                    continue
                m = re.fullmatch(r'(obl(?::arg)?|nmod|advcl(?::pred)?|acl(?::relcl)?):(.+)', edep['deprel'])
                if m:
                    bdeprel = m.group(1)
                    cdeprel = m.group(2)
                    solved = False
                    # Arabic clauses often start with وَ wa "and", which does not add
                    # much to the meaning but sometimes gets included in the enhanced
                    # case label. Remove it if there are more informative subsequent
                    # morphs.
                    cdeprel = re.sub(r'^وَ_', r'', cdeprel)
                    cdeprel = re.sub(r'^وَ:', r'', cdeprel)
                    cdeprel = re.sub(r'^وَ$', r'', cdeprel)
                    edep['deprel'] = self.compose_edeprel(bdeprel, cdeprel)
                    # If one of the following expressions occurs followed by another preposition
                    # or by morphological case, remove the additional case marking.
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
                    # Split preposition from morphological case (if any), normalize
                    # the preposition and add the fixed morphological case where
                    # applicable.
                    m = re.fullmatch(r'([^:]+):(nom|gen|acc)', cdeprel)
                    adposition = m.group(1) if m else cdeprel
                    if adposition in self.unambiguous:
                        cdeprel = self.unambiguous[adposition]
                        edep['deprel'] = self.compose_edeprel(bdeprel, cdeprel)
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
