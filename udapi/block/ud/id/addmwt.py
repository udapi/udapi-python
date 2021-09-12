"""
Block ud.id.AddMwt cuts the clitic "-nya" in Indonesian (preprocessed with
MorphInd whose output is stored in MISC attribute MorphInd).
"""
import udapi.block.ud.addmwt
import logging
import re

class AddMwt(udapi.block.ud.addmwt.AddMwt):
    """Detect and mark MWTs (split them into words and add the words to the tree)."""

    def multiword_analysis(self, node):
        """Return a dict with MWT info or None if `node` does not represent a multiword token."""
        if node.upos == 'VERB' and re.search(r'nya$', node.form, re.IGNORECASE) and re.search(r'\+dia<p>_PS3\$$', node.misc['MorphInd']):
            splitform = re.sub(r'(nya)$', r' \1', node.form, flags=re.IGNORECASE)
            # For transitive verbs with the meN- prefix, -nya is an object clitic.
            # For passive verbs with the di- prefix, -nya refers to a passive agent.
            # For verbs with prefixes ber-, ter-, and verbs without prefixes, -nya is a definite article and signals nominalization.
            # The same would hold for intransitive verbs with the meN- prefix but we cannot recognize them (we will treat all meN- verbs as transitive).
            menverb = True if re.match(r'^\^meN\+', node.misc['MorphInd']) else False
            diverb = True if re.match(r'^\^di\+', node.misc['MorphInd']) else False
            nominalization = not menverb and not diverb
            # The verb with -nya typically has Number[psor]=Sing|Person[psor]=3.
            # Remove these features from the verb and give the pronoun normal features Number=Sing|Person=3.
            if node.feats['Number[psor]'] != 'Sing':
                logging.warning("Verb '%s' has Number[psor]=='%s'" % (node.form, node.feats['Number[psor]']))
            if node.feats['Person[psor]'] != '3':
                logging.warning("Verb '%s' has Person[psor]=='%s'" % (node.form, node.feats['Person[psor]']))
            node.feats['Number[psor]'] = ''
            node.feats['Person[psor]'] = ''
            if nominalization:
                lemma = splitform.lower()
                upos = 'VERB DET'
                feats = '* Definite=Def|PronType=Art'
                deprel = '* det'
            else:
                lemma = re.sub(r' nya$', ' dia', splitform.lower())
                upos = 'VERB PRON'
                feats = '* Number=Sing|Person=3|PronType=Prs'
                deprel = '* obj:agent' if diverb else '* obj'
            xpos = re.sub(r'\+', ' ', node.xpos)
            # 'main': 0 ... this is the default value (the first node will be the head and inherit children)
            return {'form': splitform, 'lemma': lemma, 'upos': upos, 'feats': feats, 'xpos': xpos, 'shape': 'subtree', 'deprel': deprel}
        return None

    def postprocess_mwt(self, mwt):
        """Distribute the MorphInd analysis to the two parts so that we can later use it to fix the lemmas of verbs."""
        match = re.match(r'^\^(.*)\+(dia<p>_PS3)\$$', mwt.misc['MorphInd'])
        if match:
            mwt.words[0].misc['MorphInd'] = '^'+match.group(1)+'$'
            mwt.words[1].misc['MorphInd'] = '^'+match.group(2)+'$'
