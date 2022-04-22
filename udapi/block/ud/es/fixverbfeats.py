"""Block to fix features (and potentially lemmas) of verbs in UD Spanish-PUD."""
from udapi.core.block import Block
import logging
import re

class FixVerbFeats(Block):

    def process_node(self, node):
        """
        The features assigned to verbs in Spanish PUD are often wrong, although
        the annotation was (reportedly) done manually. For example, infinitives
        are tagged with VerbForm=Fin instead of VerbForm=Inf.
        """
        if re.match(r'^(VERB|AUX)$', node.upos):
            if re.search(r'[aei]r$', node.form, re.IGNORECASE):
                # The infinitive has no features other than VerbForm.
                node.feats = {}
                node.feats['VerbForm'] = 'Inf'
                node.lemma = node.form.lower()
            elif re.search(r'ndo$', node.form, re.IGNORECASE):
                if node.form.lower() != 'entiendo':
                    # The gerund has no features other than VerbForm.
                    # The lemma is not always straightforward but we have fixed it manually.
                    node.feats = {}
                    node.feats['VerbForm'] = 'Ger'
            elif re.search(r'([ai]d|biert|dich|fech|hech|muert|puest|vist)[oa]s?$', node.form, re.IGNORECASE):
                # The (past) participle has always Gender and Number.
                # It can be VERB/AUX (infinitive is the lemma) or ADJ (masculine singular is the lemma).
                # As a verb, it also has Tense=Past. As an adjective it does not have this feature (in AnCora; but why not?)
                gender = node.feats['Gender'] if node.feats['Gender'] else ('Masc' if re.search(r'os?$', node.form, re.IGNORECASE) else 'Fem')
                number = node.feats['Number'] if node.feats['Number'] else ('Plur' if re.search(r's$', node.form, re.IGNORECASE) else 'Sing')
                node.feats = {}
                node.feats['VerbForm'] = 'Part'
                node.feats['Tense'] = 'Past'
                node.feats['Gender'] = gender
                node.feats['Number'] = number
                if re.search(r'ad[oa]s?$', node.form, re.IGNORECASE):
                    node.lemma = re.sub(r'd[oa]s?$', 'r', node.form.lower())
