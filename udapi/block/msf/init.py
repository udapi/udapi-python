"""
Morphosyntactic features (UniDive):
Initialization. Copies features from FEATS as MSF* attributes to MISC.
"""
from udapi.core.block import Block
import re

class Init(Block):


    def process_node(self, node):
        """
        For every feature in FEATS, creates its MSF* counterpart in MISC.
        """
        for f in node.feats:
            # Only selected features will be copied. Certain features are not
            # interesting for the morphosyntactic annotation.
            if f not in ['Abbr', 'AdpType', 'Emph', 'Foreign', 'NameType', 'Style', 'Typo', 'Variant']:
                node.misc['MSF'+f] = node.feats[f]
        # We are particularly interested in the Case feature but some nominals
        # lack it (e.g. acronyms or numbers). If there is a preposition, it may
        # indicate the expected case of the nominal.
        if not node.feats['Case']:
            # Not any 'case' dependent is helpful. Here we really need single-word
            # adposition.
            adpositions = [x for x in node.children if x.udeprel == 'case' and x.upos == 'ADP']
            if len(adpositions) == 1:
                fixed = [x for x in adpositions[0].children if x.udeprel == 'fixed']
                if not fixed and adpositions[0].feats['Case']:
                    node.misc['MSFCase'] = adpositions[0].feats['Case']
        # If we did not find a preposition to help us, we may be able to read
        # the case off an adjectival modifier or determiner.
        if not node.misc['MSFCase']:
            modifiers = [x for x in node.children if x.udeprel in ['amod', 'det'] and x.feats['Case']]
            if modifiers:
                node.misc['MSFCase'] = modifiers[0].feats['Case']
        # Finally, if the above did not help, we may guess the case from the deprel of the node itself.
        if not node.misc['MSFCase']:
            if node.udeprel == 'nsubj':
                node.misc['MSFCase'] = 'Nom'
            elif node.udeprel == 'obj':
                node.misc['MSFCase'] = 'Acc'
        # If the node contains Phrase features in MISC (periphrastic verb forms
        # detected by Lenka's code), replace the MS features with them.
        phrasefeatures = [x for x in node.misc if re.match(r"^Phrase[A-Z]", x)]
        for pf in phrasefeatures:
            msf = pf
            if msf == 'PhraseForm':
                msf = 'MSFVerbForm'
            else:
                msf = re.sub(r"Phrase", 'MSF', pf)
            node.misc[msf] = node.misc[pf]
            node.misc[pf] = ''
