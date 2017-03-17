"""Block ud.el.AddMwt for heuristic detection of multi-word (σε+DET) tokens. Notice that this should be used only for converting existing conllu files. Ideally a tokenizer should have already split the MWTs. Also notice that this block does not deal with the relatively rare PRON(Person=2)+'*+PRON(Person=3, i.e. "σ'το" and "στο") MWTs."""
import udapi.block.ud.addmwt

MWTS = {
    'στη': {'form'  : 'σ τη', 
            'lemma' : 'σε ο', 
            'upos'  : 'ADP DET',  
            'xpos'  : 'AsPpSp AtDf',
            'feats' : '_ Case=Acc|Gender=Fem|Number=Sing', 
            'deprel': 'case det', 
            'main'  : 0, # which of the two words will inherit the original children (if any)
            'shape' : 'siblings', # the newly created nodes will be siblings},	
            },
    'στην':  {'form': 'σ την',  'lemma': 'σε ο',  'upos':'ADP DET', 'xpos':'AsPpSp AtDf', 'feats': '_ Case=Acc|Gender=Fem|Number=Sing',  'deprel': 'case det', 'main': 0,  'shape': 'siblings'},   
    'στις':  {'form': 'σ τις',  'lemma': 'σε ο',  'upos':'ADP DET', 'xpos':'AsPpSp AtDf', 'feats': '_ Case=Acc|Gender=Fem|Number=Plur',  'deprel': 'case det', 'main': 0,  'shape': 'siblings'},   
    'στα':   {'form': 'σ τα',   'lemma': 'σε ο',  'upos':'ADP DET', 'xpos':'AsPpSp AtDf', 'feats': '_ Case=Acc|Gender=Neut|Number=Plur', 'deprel': 'case det', 'main': 0,  'shape': 'siblings'},
    'στους': {'form': 'σ τους', 'lemma': 'σε ο',  'upos':'ADP DET', 'xpos':'AsPpSp AtDf', 'feats': '_ Case=Acc|Gender=Masc|Number=Plur', 'deprel': 'case det', 'main': 0,  'shape': 'siblings'},
    'στον':  {'form': 'σ τον',  'lemma': 'σε ο',  'upos':'ADP DET', 'xpos':'AsPpSp AtDf', 'feats': '_ Case=Acc|Gender=Masc|Number=Sing', 'deprel': 'case det', 'main': 0,  'shape': 'siblings'},
}

#for v in MWTS.values():
#    pass

class AddMwt(udapi.block.ud.addmwt.AddMwt):
    """Detect and mark MWTs (split them into words and add the words to the tree)."""

    def multiword_analysis(self, node):
        """Return a dict with MWT info or None if `node` does not represent a multiword token."""
        analysis = MWTS.get(node.form.lower(), None)
        if analysis is not None:
            return analysis

        # Write a rule for ambigous prep+article MWTs
        if node.form.lower() == 'στο' and node.feats['Gender'] == 'Masc':
            return {
                'form': 'σ το','lemma': 'σε ο','upos': 'ADP DET','xpos': 'AsPpSp AtDf','deprel': 'case det','main': 0,'shape': 'siblings',
                'feats': '_ Case=Acc|Gender=Masc|Number=Sing',
            }
        elif node.form.lower() == 'στο':
            return {
                'form': 'σ το','lemma': 'σε ο','upos': 'ADP DET','xpos': 'AsPpSp AtDf','deprel': 'case det','main': 0,'shape': 'siblings',
                'feats': '_ Case=Acc|Gender=Neut|Number=Sing',
            }
            
        return None

#    def postprocess_mwt(self, mwt):
#        pass
