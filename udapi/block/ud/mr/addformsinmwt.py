"""
Block ud.mr.AddFormsInMwt looks for multiword tokens whose words lack forms.
Based on the form of the surface token and on the information provided in
the lemmas and UPOS, tries to reconstruct the forms of individual words.
"""
from udapi.core.block import Block
import re
import logging


class AddFormsInMwt(Block):
    """Guess forms of syntactic worms within a multiword token."""

    def process_node(self, node):
        if node.form == '_' and node.multiword_token:
            mwt = node.multiword_token
            # Many multiword tokens consist of NOUN + ADP. Beware: The adposition
            # may have a form different from its lemma. It happens with possessive
            # postpositions चा, चे, which distinguish the gender and number of
            # the possessed entity.
            if len(mwt.words) == 2 and mwt.words[1].upos == 'ADP':
                if mwt.words[1].lemma == 'चा':
                    m = re.match(r'^(.+)(चा|चे|च्या|ची)$', mwt.form)
                    if m:
                        if node == mwt.words[0]:
                            node.form = m.group(1)
                        else:
                            node.form = m.group(2)
                    else:
                        logging.info("Cannot decompose %s+ADP multiword token '%s'. Part lemmas are '%s' and '%s'." % (mwt.words[0].upos, mwt.form, mwt.words[0].lemma, mwt.words[1].lemma))
                else: # not the possessive 'ca'
                    m = re.match(r'^(.+)' + mwt.words[1].lemma + r'$', mwt.form)
                    if m:
                        if node == mwt.words[0]:
                            node.form = m.group(1)
                        else:
                            node.form = node.lemma
                    else:
                        logging.info("Cannot decompose %s+ADP multiword token '%s'. Part lemmas are '%s' and '%s'." % (mwt.words[0].upos, mwt.form, mwt.words[0].lemma, mwt.words[1].lemma))
            else:
                logging.info("Cannot decompose multiword token '%s' of %d parts: %s" % (mwt.form, len(mwt.words), str([x.lemma + '/' + x.upos for x in mwt.words])))
