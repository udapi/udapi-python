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
            # The verb with -nya typically has Number[psor]=Sing|Person[psor]=3.
            # Remove these features from the verb and give the pronoun normal features Number=Sing|Person=3.
            if node.feats['Number[psor]'] != 'Sing':
                logging.warning("Verb '%s' has Number[psor]=='%s'" % (node.form, node.feats['Number[psor]']))
            if node.feats['Person[psor]'] != '3':
                logging.warning("Verb '%s' has Person[psor]=='%s'" % (node.form, node.feats['Person[psor]']))
            node.feats['Number[psor]'] = ''
            node.feats['Person[psor]'] = ''
            pronfeats = 'Number=Sing|Person=3|PronType=Prs'
            xpos = re.sub(r'\+', ' ', node.xpos)
            deprel = 'obl:agent' if re.match(r'^\^di\+', node.misc['MorphInd']) else 'obj'
            # 'main': 0 ... this is the default value (the first node will be the head and inherit children)
            return {'form': splitform, 'lemma': splitform, 'upos': 'VERB PRON', 'feats': '* '+pronfeats, 'xpos': xpos, 'shape': 'subtree', 'deprel': '* '+deprel}
        return None

    def postprocess_mwt(self, mwt):
        """Distribute the MorphInd analysis to the two parts so that we can later use it to fix the lemmas of verbs."""
        match = re.match(r'^\^(.*)\+(dia<p>_PS3)\$$', mwt.misc['MorphInd'])
        if match:
            mwt.words[0].misc['MorphInd'] = '^'+match.group(1)+'$'
            mwt.words[1].misc['MorphInd'] = '^'+match.group(2)+'$'
