"""
Some UD treebanks use features PunctType and PunctSide that classify
punctuation symbols. This block can be used to add such features to data where
they are missing – the classification is mostly deterministic. If the input
data already contains such features, their values will be overwritten.
"""
from udapi.core.block import Block

# TODO We need to know the language, there are many other quotation styles,
#      e.g. Finnish and Swedish uses the same symbol for opening and closing: ”X”.
#      Danish uses uses the French quotes, but switched: »X«.

PUNCT_TYPES = {
    '(': 'Brck',
    ')': 'Brck',
    '[': 'Brck',
    ']': 'Brck',
    '{': 'Brck',
    '}': 'Brck',
    '.': 'Peri',
    '...': 'Elip',
    '…': 'Elip',
    ',': 'Comm',
    ';': 'Semi',
    ':': 'Colo',
    '!': 'Excl',
    '¡': 'Excl', # Spanish initial exclamation mark
    '?': 'Qest',
    '¿': 'Qest', # Spanish initial question mark
    '/': 'Colo', # it is used this way in AnCora
    '-': 'Dash',
    '–': 'Dash',
    '—': 'Dash',
    '"': 'Quot',
    "'": 'Quot',
    '`': 'Quot',
    '“': 'Quot', # opening English, closing Czech
    '”': 'Quot', # closing English
    '„': 'Quot', # opening Czech
    '‘': 'Quot', # opening English, closing Czech
    '’': 'Quot', # closing English
    '‚': 'Quot', # opening Czech
    '«': 'Quot', # opening French, closing Danish
    '»': 'Quot', # closing French, opening Danish
    '‹': 'Quot',
    '›': 'Quot',
    '《': 'Quot', # Korean, Chinese
    '》': 'Quot',
    '「': 'Quot', # Chinese, Japanese
    '」': 'Quot',
    '『': 'Quot',
    '』': 'Quot'
}

PUNCT_SIDES = {
    '(': 'Ini',
    ')': 'Fin',
    '[': 'Ini',
    ']': 'Fin',
    '{': 'Ini',
    '}': 'Fin',
    '¡': 'Ini', # Spanish initial exclamation mark
    '!': 'Fin', # but outside Spanish people may expect empty value
    '¿': 'Ini', # Spanish initial question mark
    '?': 'Fin',
    '《': 'Ini', # Korean, Chinese
    '》': 'Fin',
    '「': 'Ini', # Chinese, Japanese
    '」': 'Fin',
    '『': 'Ini',
    '』': 'Fin'
}


class AddPunctType(Block):
    """Add features PunctType and PunctSide where applicable."""

    def process_node(self, node):
        # The two features apply only to PUNCT. If they already occur elsewhere, erase them.
        if node.upos != 'PUNCT':
            node.feats['PunctType'] = ''
            node.feats['PunctSide'] = ''
        else:
            if node.form in PUNCT_TYPES:
                node.feats['PunctType'] = PUNCT_TYPES[node.form]
            else:
                node.feats['PunctType'] = ''
            if node.form in PUNCT_SIDES:
                node.feats['PunctSide'] = PUNCT_SIDES[node.form]
            else:
                node.feats['PunctSide'] = ''
