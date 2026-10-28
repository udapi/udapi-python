"""
This block checks Spanish data for clitic doubling, i.e., the same argument is
encoded concurrently by a pronominal clitic and by a full nominal, as in
"Pedro le dio un libro a Isabel" = lit. "Pedro her gave a book to Isabel."
In such cases, the clitic should be expl and the full nominal should be obl:arg
(if the clitic is in dative) or obj (if the clitic is in accusative).
The block targets a systematic error in AnCora.
"""
from udapi.core.block import Block

class FixCliticDoubling(Block):

    def process_node(self, node):
        if node.upos == 'VERB':
            dative_clitics = [x for x in node.children if x.form.lower() in ['le', 'les', 'se'] and x.deprel == 'obl:arg']
            #accusative_clitics = [x for x in node.children if x.form.lower() in ['lo', 'la', 'los', 'las']]
            a_nominals = [x for x in node.children if x.deprel == 'obl:arg' and len([y for y in x.children if y.form.lower() == 'a' and y.deprel == 'case']) > 0]
            if len(dative_clitics) == 1 and len(a_nominals) == 1:
                dative_clitics[0].deprel = 'expl'
                if dative_clitics[0].deps:
                    dative_clitics[0].deps[0]['deprel'] = 'expl'
