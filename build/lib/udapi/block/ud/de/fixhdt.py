"""
Block to fix annotation of UD German-HDT.

It was created independently of ud.de.AddMwt but it aims to do essentially the
same thing. Future work: make the two blocks converge.

Currently known differences:
- This block covers a wider range of contractions.
- This block generates morphological features for the syntactic words.
- This block does not touch words that look like contractions but do not have PronType=Art (this is a reliable indicator in HDT).
- This block overrides the default attachment when the original relation is root, conj, reparandum.
- The other block takes advantage of the generic class ud.AddMwt, so it does not have to re-invent common procedures.
"""
from udapi.core.block import Block
import logging
import re

class FixHDT(Block):

    def process_node(self, node):
        # PronType=Art with ADP is wrong. Fused prepositions and articles should be decomposed in UD.
        # The following contractions have been observed:
        # a. am ans aufs beim durchs fürs hinterm hinters im ins übers ums unterm unters vom vorm vors z. zum zur
        if node.upos == 'ADP' and node.feats['PronType'] == 'Art':
            if re.match("^(a\.|am|ans|aufs|beim|durchs|fürs|hinter[ms]|im|ins|übers|ums|unter[ms]|vom|vor[ms]|z\.|zu[mr])$", node.form, re.IGNORECASE):
                # We need two nodes instead of one. Create a node.
                # The parent should not be the root but unfortunately it is not guaranteed.
                node2 = node.create_child()
                node2.shift_after_node(node)
                if not re.match(r"^(root|conj|reparandum)$", node.udeprel):
                    node2.parent = node.parent
                    node.deprel = 'case'
                node2.deprel = 'det'
                mwt = node.root.create_multiword_token(form=node.form, words=[node, node2], misc=node.misc)
                node.misc['SpaceAfter'] = ''
                # We want to respect the original letter case in the forms of the syntactic words.
                # We can use the isupper() method to find out whether all letters are uppercase.
                # However, detecting first-letter capitalization requires more work.
                up = 2 if mwt.form.isupper() else 1 if mwt.form[:1].isupper() else 0
                up2 = 2 if up == 2 else 0
                if re.match(r"^(a\.|am|ans)$", mwt.form, re.IGNORECASE):
                    node.form = mimic_case(up, 'an')
                    node.lemma = 'an'
                elif re.match(r"^aufs$", mwt.form, re.IGNORECASE):
                    node.form = mimic_case(up, 'auf')
                    node.lemma = 'auf'
                elif re.match(r"^beim$", mwt.form, re.IGNORECASE):
                    node.form = mimic_case(up, 'bei')
                    node.lemma = 'bei'
                elif re.match(r"^durchs$", mwt.form, re.IGNORECASE):
                    node.form = mimic_case(up, 'durch')
                    node.lemma = 'durch'
                elif re.match(r"^fürs$", mwt.form, re.IGNORECASE):
                    node.form = mimic_case(up, 'für')
                    node.lemma = 'für'
                elif re.match(r"^hinter[ms]$", mwt.form, re.IGNORECASE):
                    node.form = mimic_case(up, 'hinter')
                    node.lemma = 'hinter'
                elif re.match(r"^(im|ins)$", mwt.form, re.IGNORECASE):
                    node.form = mimic_case(up, 'in')
                    node.lemma = 'in'
                elif re.match(r"^übers$", mwt.form, re.IGNORECASE):
                    node.form = mimic_case(up, 'über')
                    node.lemma = 'über'
                elif re.match(r"^ums$", mwt.form, re.IGNORECASE):
                    node.form = mimic_case(up, 'um')
                    node.lemma = 'um'
                elif re.match(r"^unter[ms]$", mwt.form, re.IGNORECASE):
                    node.form = mimic_case(up, 'unter')
                    node.lemma = 'unter'
                elif re.match(r"^vom$", mwt.form, re.IGNORECASE):
                    node.form = mimic_case(up, 'von')
                    node.lemma = 'von'
                elif re.match(r"^vor[ms]$", mwt.form, re.IGNORECASE):
                    node.form = mimic_case(up, 'vor')
                    node.lemma = 'vor'
                elif re.match(r"^(z\.|zu[mr])$", mwt.form, re.IGNORECASE):
                    node.form = mimic_case(up, 'zu')
                    node.lemma = 'zu'
                node.upos = 'ADP'
                node.xpos = 'APPR'
                node.feats = '_'
                node.feats['AdpType'] = 'Prep'
                # We must use search() because match() only checks at the beginning of the string.
                if re.search("[m\.]$", mwt.form, re.IGNORECASE):
                    node2.form = mimic_case(up2, 'dem')
                    node2.feats = 'Case=Dat|Definite=Def|Gender=Masc,Neut|Number=Sing|PronType=Art'
                    node.feats['Case'] = 'Dat'
                    node2.lemma = 'der'
                elif re.search("s$", mwt.form, re.IGNORECASE):
                    node2.form = mimic_case(up2, 'das')
                    node2.feats = 'Case=Acc|Definite=Def|Gender=Neut|Number=Sing|PronType=Art'
                    node.feats['Case'] = 'Acc'
                    node2.lemma = 'der'
                elif re.search("r$", mwt.form, re.IGNORECASE):
                    node2.form = mimic_case(up2, 'der')
                    node2.feats = 'Case=Dat|Definite=Def|Gender=Fem|Number=Sing|PronType=Art'
                    node.feats['Case'] = 'Dat'
                    node2.lemma = 'der'
                node2.upos = 'DET'
                node2.xpos = 'ART'

def mimic_case(up, x):
    if up >= 2:
        return x.upper()
    elif up == 1:
        return x[:1].upper() + x[1:].lower()
    else:
        return x.lower()
