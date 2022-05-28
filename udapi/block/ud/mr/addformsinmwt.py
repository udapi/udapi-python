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
            if len(mwt.words) == 2 and re.match(r'^(ADP|PART)$', mwt.words[1].upos):
                # Occasionally the lemma of the possessive postposition is mistakenly 'ची' instead of 'चा'.
                if mwt.words[1].lemma == 'चा' or mwt.words[1].lemma == 'ची':
                    mwt.words[1].lemma = 'चा'
                    # चा (cā) ... Masc Sing
                    # ची (cī) ... Fem Sing, Neut Plur
                    # चे (ce) ... Neut Sing, Masc Plur
                    # च्या (cyā) ... Fem Plur
                    # चं (caṁ) ... ?
                    m = re.match(r'^(.+)(चा|ची|चे|च्या|चं)$', mwt.form)
                    # The resulting form is different with personal pronouns.
                    # माझा (mājhā), माझी (mājhī), माझे (mājhe), माझ्या (mājhyā)
                    # तुझी (tujhī), तुझे (tujhe)
                    # आपला (āpalā), आपली (āpalī), आपल्या (āpalyā)
                    # त्याचं (tyācaṁ)
                    m2 = re.match(r'^(माझ|तुझ|आपल)(ा|ी|े|्या)$', mwt.form)
                    if m:
                        if node == mwt.words[0]:
                            node.form = m.group(1)
                        else:
                            node.form = m.group(2)
                    elif m2:
                        if node == mwt.words[0]:
                            node.form = m2.group(1)
                        else:
                            node.form = 'च' + m2.group(2)
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
            elif len(mwt.words) == 3 and re.match(r'^(ADP|PART)$', mwt.words[1].upos) and re.match(r'^(ADP|PART)$', mwt.words[2].upos):
                # Compound postpositions where the middle word is the possessive 'चा'.
                if mwt.words[1].lemma == 'चा':
                    m = re.match(r'^(.+)(चा|ची|चे|च्या|चं)(.+)$', mwt.form)
                    m2 = re.match(r'^(माझ|तुझ|आपल)(ा|ी|े|्या)$', mwt.form)
                    if m:
                        if node == mwt.words[0]:
                            node.form = m.group(1)
                        elif node == mwt.words[1]:
                            node.form = m.group(2)
                        else:
                            node.form = m.group(3)
                    elif m2:
                        if node == mwt.words[0]:
                            node.form = m2.group(1)
                        elif node == mwt.words[1]:
                            node.form = 'च' + m2.group(2)
                        else:
                            node.form = m2.group(3)
                    else:
                        logging.info("Cannot decompose %s+%s+%s multiword token '%s'. Part lemmas are '%s', '%s', and '%s'." % (mwt.words[0].upos, mwt.words[1].upos, mwt.words[2].upos, mwt.form, mwt.words[0].lemma, mwt.words[1].lemma, mwt.words[1].lemma))
            else:
                logging.info("Cannot decompose multiword token '%s' of %d parts: %s" % (mwt.form, len(mwt.words), str([x.lemma + '/' + x.upos for x in mwt.words])))
