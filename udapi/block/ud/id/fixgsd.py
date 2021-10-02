"""Block to fix annotation of UD Indonesian-GSD."""
from udapi.core.block import Block
import logging
import re

class FixGSD(Block):

    def fix_upos_based_on_morphind(self, node):
        """
        Example from data: ("kesamaan"), the correct UPOS is NOUN, as
        suggested by MorphInd.
        Based on my observation so far, if there is a different UPOS between
        the original GSD and MorphInd, it's better to trust MorphInd
        I found so many incorrect UPOS in GSD, especially when NOUNs become
        VERBs and VERBs become NOUNs.
        I suggest adding Voice=Pass when the script decides ke-xxx-an as VERB.
        """
        if node.upos == 'VERB' and node.xpos == 'NSD' and re.match(r'^ke.+an$', node.form, re.IGNORECASE):
            node.upos = 'NOUN'
            if node.udeprel == 'acl':
                node.deprel = 'nmod'
            elif node.udeprel == 'advcl':
                node.deprel = 'obl'

    def fix_ordinal_numerals(self, node):
        """
        Ordinal numerals should be ADJ NumType=Ord in UD. They have many different
        UPOS tags in Indonesian GSD. This method harmonizes them.
        pertama = first
        kedua = second
        ketiga = third
        keempat = fourth
        kelima = fifth
        keenam = sixth
        ketujuh = seventh
        kedelapan = eighth
        kesembilan = ninth
        ke-48 = 48th

        However! The ke- forms (i.e., not 'pertama') can also function as total
        versions of cardinal numbers ('both', 'all three' etc.). If the numeral
        precedes the noun, it is a total cardinal; if it follows the noun, it is
        an ordinal. An exception is when the modified noun is 'kali' = 'time'.
        Then the numeral is ordinal regardless where it occurs, and together
        with 'kali' it functions as an adverbial ordinal ('for the second time').
        """
        # We could also check the XPOS, which is derived from MorphInd: re.match(r'^CO-', node.xpos)
        if re.match(r'^pertama(nya)?$', node.form, re.IGNORECASE):
            node.upos = 'ADJ'
            node.feats['NumType'] = 'Ord'
            if re.match(r'^(det|nummod|nmod)$', node.udeprel):
                node.deprel = 'amod'
        elif re.match(r'^(kedua|ketiga|keempat|kelima|keenam|ketujuh|kedelapan|kesembilan|ke-?\d+)(nya)?$', node.form, re.IGNORECASE):
            if node.parent.ord < node.ord or node.parent.lemma == 'kali':
                node.upos = 'ADJ'
                node.feats['NumType'] = 'Ord'
                if re.match(r'^(det|nummod|nmod)$', node.udeprel):
                    node.deprel = 'amod'
            else:
                node.upos = 'NUM'
                node.feats['NumType'] = 'Card'
                node.feats['PronType'] = 'Tot'
                if re.match(r'^(det|amod|nmod)$', node.udeprel):
                    node.deprel = 'nummod'
        # The following is not an ordinal numeral but I am too lazy to create a separate method for that.
        elif node.form.lower() == 'semua':
            # It means 'all'. Originally it was DET, PRON, or ADV.
            node.upos = 'DET'
            node.feats['PronType'] = 'Tot'
            if node.udeprel == 'nmod' or node.udeprel == 'advmod':
                node.deprel = 'det'

    def rejoin_ordinal_numerals(self, node):
        """
        If an ordinal numeral is spelled using digits ('ke-18'), it is often
        tokenized as multiple tokens, which is wrong. Fix it.
        """
        if node.form.lower() == 'ke':
            dash = None
            number = None
            if node.next_node:
                if node.next_node.form == '-':
                    dash = node.next_node
                    if dash.next_node and re.match(r'^\d+$', dash.next_node.form):
                        number = dash.next_node
                        node.form = node.form + dash.form + number.form
                        node.lemma = node.lemma + dash.lemma + number.lemma
                elif re.match(r'^\d+$', node.next_node.form) and (node.parent == node.next_node or node.next_node.parent == node):
                    number = node.next_node
                    node.feats['Typo'] = 'Yes'
                    node.misc['CorrectForm'] = node.form + '-' + number.form
                    node.form = node.form + number.form
                    node.lemma = node.lemma + '-' + number.lemma
                if number:
                    # Let us pretend that these forms are always ordinal numerals.
                    # Situations where they act as total cardinals will be disambiguated
                    # in a subsequent call to fix_ordinal_numerals().
                    node.upos = 'ADJ'
                    node.xpos = 'CO-'
                    node.feats['NumType'] = 'Ord'
                    node.misc['MorphInd'] = '^ke<r>_R--+' + number.form + '<c>_CC-$'
                    # Find the parent node. Assume that the dash, if present, was not the head.
                    if node.parent == number:
                        node.parent = number.parent
                        node.deprel = number.deprel
                    if re.match(r'(case|mark|det|nummod|nmod)', node.udeprel):
                        node.deprel = 'amod'
                    # Adjust SpaceAfter.
                    node.misc['SpaceAfter'] = 'No' if number.no_space_after else ''
                    # Remove the separate node of the dash and the number.
                    if dash:
                        if len(dash.children) > 0:
                            for c in dash.children:
                                c.parent = node
                        dash.remove()
                    if len(number.children) > 0:
                        for c in number.children:
                            c.parent = node
                    number.remove()
                    # There may have been spaces around the dash, which are now gone. Recompute the sentence text.
                    node.root.text = node.root.compute_text()

    def rejoin_decades(self, node):
        """
        In Indonesian, the equivalent of English "1990s" is written as "1990-an".
        In GSD, it is often tokenized as multiple tokens, which is wrong. Fix it.
        """
        if node.form.lower() == 'an':
            dash = None
            number = None
            if node.prev_node:
                if node.prev_node.form == '-':
                    dash = node.prev_node
                    if dash.prev_node and re.match(r'^\d+$', dash.prev_node.form):
                        number = dash.prev_node
                        node.form = number.form + dash.form + node.form
                        node.lemma = number.lemma + dash.lemma + node.lemma
                elif re.match(r'^\d+$', node.prev_node.form) and (node.parent == node.prev_node or node.prev_node.parent == node):
                    number = node.prev_node
                    node.feats['Typo'] = 'Yes'
                    node.misc['CorrectForm'] = number.form + '-' + node.form
                    node.form = number.form + node.form
                    node.lemma = number.lemma + '-' + node.lemma
                if number:
                    # The combined token is no longer a numeral. It cannot quantify an entity.
                    # Instead, it is itself something like a noun (or perhaps proper noun).
                    node.upos = 'NOUN'
                    node.xpos = 'NSD'
                    node.feats['NumType'] = ''
                    # In some cases, "-an" is labeled as foreign for no obvious reason.
                    node.feats['Foreign'] = ''
                    node.misc['MorphInd'] = '^' + number.form + '<c>_CC-+an<f>_F--$'
                    # Find the parent node. Assume that the dash, if present, was not the head.
                    if node.parent == number:
                        node.parent = number.parent
                        node.deprel = number.deprel
                    if re.match(r'(case|mark|det|nummod|nmod)', node.udeprel):
                        node.deprel = 'nmod'
                    # No need to adjust SpaceAfter, as the 'an' node was the last one in the complex.
                    #node.misc['SpaceAfter'] = 'No' if number.no_space_after else ''
                    # Remove the separate node of the dash and the number.
                    if dash:
                        if len(dash.children) > 0:
                            for c in dash.children:
                                c.parent = node
                        dash.remove()
                    if len(number.children) > 0:
                        for c in number.children:
                            c.parent = node
                    number.remove()
                    # There may have been spaces around the dash, which are now gone. Recompute the sentence text.
                    node.root.text = node.root.compute_text()

    def lemmatize_verb_from_morphind(self, node):
        # The MISC column contains the output of MorphInd for the current word.
        # The analysis has been interpreted wrongly for some verbs, so we need
        # to re-interpret it and extract the correct lemma.
        if node.upos == "VERB":
            morphind = node.misc["MorphInd"]
            if morphind:
                # Remove the start and end tags from morphind.
                morphind = re.sub(r"^\^", "", morphind)
                morphind = re.sub(r"\$$", "", morphind)
                # Remove the final XPOS tag from morphind.
                morphind = re.sub(r"_V[SP][AP]$", "", morphind)
                # Split morphind to prefix, stem, and suffix.
                morphemes = re.split(r"\+", morphind)
                # Expected suffixes are -kan, -i, -an, or no suffix at all.
                # There is also the circumfix ke-...-an which seems to be nominalized adjective:
                # "sama" = "same, similar"; "kesamaan" = "similarity", lemma is "sama";
                # but I am not sure what is the reason that these are tagged VERB.
                if len(morphemes) > 1 and re.match(r"^(kan|i|an(_NSD)?)$", morphemes[-1]):
                    del morphemes[-1]
                # Expected prefixes are meN-, di-, ber-, peN-, ke-, ter-, se-, or no prefix at all.
                # There can be two prefixes in a row, e.g., "ber+ke+", or "ter+peN+".
                while len(morphemes) > 1 and re.match(r"^(meN|di|ber|peN|ke|ter|se|per)$", morphemes[0]):
                    del morphemes[0]
                # Check that we are left with just one morpheme.
                if len(morphemes) != 1:
                    logging.warning("One morpheme expected, found %d %s, morphind = '%s', form = '%s', feats = '%s'" % (len(morphemes), morphemes, morphind, node.form, node.feats))
                else:
                    lemma = morphemes[0]
                    # Remove the stem POS category.
                    lemma = re.sub(r"<[a-z]+>(_.*)?$", "", lemma)
                    node.lemma = lemma
            else:
                logging.warning("No MorphInd analysis found for form '%s'" % (node.form))

    def merge_reduplicated_plural(self, node):
        # Instead of compound:plur, merge the reduplicated plurals into a single token.
        if node.deprel == "compound:plur":
            root = node.root
            # We assume that the previous token is a hyphen and the token before it is the parent.
            first = node.parent
            if first.ord == node.ord-2 and first.form.lower() == node.form.lower():
                hyph = node.prev_node
                if hyph.is_descendant_of(first) and re.match(r"^(-|–|--)$", hyph.form):
                    # Neither the hyphen nor the current node should have children.
                    # If they do, re-attach the children to the first node.
                    for c in hyph.children:
                        c.parent = first
                    for c in node.children:
                        c.parent = first
                    # Merge the three nodes.
                    first.form = first.form + "-" + node.form
                    first.feats["Number"] = "Plur"
                    if node.no_space_after:
                        first.misc["SpaceAfter"] = "No"
                    else:
                        first.misc["SpaceAfter"] = ""
                    hyph.remove()
                    node.remove()
                    # We cannot be sure whether the original annotation correctly said that there are no spaces around the hyphen.
                    # If it did not, then we have a mismatch with the sentence text, which we must fix.
                    # The following will also fix cases where there was an n-dash ('–') instead of a hyphen ('-').
                    root.text = root.compute_text()

    def fix_plural_propn(self, node):
        """
        It is unlikely that a proper noun will have a plural form in Indonesian.
        All examples observed in GSD should actually be tagged as common nouns.
        """
        if node.upos == 'PROPN' and node.feats['Number'] == 'Plur':
            node.upos = 'NOUN'
            node.lemma = node.lemma.lower()
        if node.upos == 'PROPN':
            node.feats['Number'] = ''

    def fix_satu_satunya(self, node):
        """
        'satu' = 'one' (NUM)
        'satu-satunya' = 'the only'
        """
        root = node.root
        if node.form == 'nya' and node.parent.form.lower() == 'satu' and node.parent.udeprel == 'fixed' and node.parent.parent.form.lower() == 'satu':
            satu0 = node.parent.parent
            satu1 = node.parent
            nya = node
            dash = None
            if satu1.ord == satu0.ord+2 and satu1.prev_node.form == '-':
                dash = satu1.prev_node
                satu0.misc['SpaceAfter'] = 'No'
                dash.misc['SpaceAfter'] = 'No'
                root.text = root.compute_text()
            satu1.deprel = 'compound:redup'
            nya.parent = satu0
        # We actually cannot leave the 'compound:redup' here because it is not used in Indonesian.
        if node.form == 'nya' and node.parent.form.lower() == 'satu':
            satu0 = node.parent
            nya = node
            if satu0.next_node.form == '-':
                dash = satu0.next_node
                if dash.next_node.form.lower() == 'satu':
                    satu1 = dash.next_node
                    if satu1.ord == node.ord-1:
                        # Merge satu0 + dash + satu1 into one node.
                        satu0.form = satu0.form + dash.form + satu1.form
                        dash.remove()
                        satu1.remove()
                        # There should be a multi-word token comprising satu1 + nya.
                        mwt = nya.multiword_token
                        if mwt:
                            mwtmisc = mwt.misc.copy()
                            mwt.remove()
                            mwt = root.create_multiword_token([satu0, nya], satu0.form + nya.form, mwtmisc)
                            satu0.misc['SpaceAfter'] = ''
                        root.text = root.compute_text()
        if node.multiword_token and node.no_space_after:
            node.misc['SpaceAfter'] = ''

    def process_node(self, node):
        self.fix_plural_propn(node)
        self.fix_upos_based_on_morphind(node)
        self.rejoin_ordinal_numerals(node)
        self.fix_ordinal_numerals(node)
        self.rejoin_decades(node)
        self.lemmatize_verb_from_morphind(node)
        self.fix_satu_satunya(node)
