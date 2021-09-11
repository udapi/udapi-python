"""
Block ud.id.AddMwt cuts the clitic "-nya" in Indonesian (preprocessed with
MorphInd whose output is stored in MISC attribute MorphInd).
"""
import udapi.block.ud.addmwt

class AddMwt(udapi.block.ud.addmwt.AddMwt):
    """Detect and mark MWTs (split them into words and add the words to the tree)."""

    def multiword_analysis(self, node):
        """Return a dict with MWT info or None if `node` does not represent a multiword token."""
        if node.upos == 'VERB' and re.search(r'nya$', node.form, re.IGNORECASE):
            splitform = re.sub(r'(nya)$', r' \1', re.IGNORECASE)
            # 'main': 0 ... this is the default value (the first node will be the head and inherit children)
            return {'form': splitform, 'lemma': splitform, 'upos': 'VERB PRON', 'shape': 'subtree', 'deprel': '* obj'}
        return None
