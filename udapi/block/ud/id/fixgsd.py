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

    def fix_semua(self, node):
        """
        Indonesian "semua" means "everything, all".
        Originally it was DET, PRON, or ADV.
        Ika: I usually only labeled "semua" as DET only if it's followed by a
        NOUN/PROPN. If it's followed by DET (including '-nya' as DET) or it's
        not followed by any NOUN/DET, I labeled them as PRON.
        """
        if node.form.lower() == 'semua':
            if re.match(r'^(NOUN|PROPN)$', node.parent.upos) and node.parent.ord > node.ord:
                node.upos = 'DET'
                if node.udeprel == 'nmod' or node.udeprel == 'advmod':
                    node.deprel = 'det'
            else:
                node.upos = 'PRON'
                if node.udeprel == 'det' or node.udeprel == 'advmod':
                    node.deprel = 'nmod'
            node.feats['PronType'] = 'Tot'

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

    def merge_reduplication(self, node):
        """
        Reduplication is a common morphological device in Indonesian. Reduplicated
        nouns signal plural but some reduplications also encode emphasis, modification
        of meaning etc. In the previous annotation of GSD, reduplication was mostly
        analyzed as three tokens, e.g., for plurals, the second copy would be attached
        to the first one as compound:plur, and the hyphen would be attached to the
        second copy as punct. We want to analyze reduplication as a single token.
        Fix it.
        """
        # We assume that the previous token is a hyphen and the token before it is the parent.
        first = node.parent
        root = node.root
        # Example of identical reduplication: negara-negara = countries
        # Example of reduplication with -an: kopi-kopian = various coffee trees
        # Example of reduplication with vowel substitution: bolak-balik = alternating
        # Example of reduplication with di-: disebut-sebut = mentioned (the verb sebut is reduplicated, then passivized)
        # Example of reduplication with se-: sehari-hari = daily (hari = day)
        # The last pattern is not reduplication but we handle it here because the procedure is very similar: non-/sub-/anti- + a word.
        if first.ord == node.ord-2 and (first.form.lower() == node.form.lower() or first.form.lower() + 'an' == node.form.lower() or re.match(r'^(.)o(.)a(.)-\1a\2i\3$', first.form.lower() + '-' + node.form.lower()) or first.form.lower() == 'di' + node.form.lower() or first.form.lower() == 'se' + node.form.lower() or re.match(r'^(non|sub|anti|multi|kontra)$', first.form.lower())):
            hyph = node.prev_node
            if hyph.is_descendant_of(first) and re.match(r'^(-|–|--)$', hyph.form):
                # This is specific to the reduplicated plurals. The rest will be done for any reduplications.
                # Note that not all reduplicated plurals had compound:plur. So we will look at whether they are NOUN.
                ###!!! Also, reduplicated plural nouns always have exact copies on both sides of the hyphen.
                ###!!! Some other reduplications have slight modifications on one or the other side.
                if node.upos == 'NOUN' and first.form.lower() == node.form.lower():
                    first.feats['Number'] = 'Plur'
                # For the non-/sub-/anti- prefix we want to take the morphology from the second word.
                if re.match(r'^(non|sub|anti|multi|kontra)$', first.form.lower()):
                    first.lemma = first.lemma + '-' + node.lemma
                    first.upos = node.upos
                    first.xpos = node.xpos
                    first.feats = node.feats
                    first.misc['MorphInd'] = re.sub(r'\$\+\^', '+', first.misc['MorphInd'] + '+' + node.misc['MorphInd'])
                # Neither the hyphen nor the current node should have children.
                # If they do, re-attach the children to the first node.
                for c in hyph.children:
                    c.parent = first
                for c in node.children:
                    c.parent = first
                # Merge the three nodes.
                # It is possible that the last token of the original annotation
                # is included in a multi-word token. Then we must extend the
                # multi-word token to the whole reduplication! Example:
                # pemeran-pemerannya (the actors) ... originally 'pemeran' and '-'
                # are tokens, 'pemerannya' is a MWT split to 'pemeran' and 'nya'.
                mwt = node.multiword_token
                if mwt:
                    # We assume that the MWT has only two words. We are not prepared for other possibilities.
                    if len(mwt.words) > 2:
                        logging.critical('MWT of only two words is expected')
                    mwtmisc = mwt.misc.copy()
                    second = mwt.words[1]
                    mwt.remove()
                    first.form = first.form + '-' + node.form
                    hyph.remove()
                    node.remove()
                    first.misc['SpaceAfter'] = ''
                    mwt = root.create_multiword_token([first, second], first.form + second.form, mwtmisc)
                else:
                    first.form = first.form + '-' + node.form
                    if node.no_space_after:
                        first.misc['SpaceAfter'] = 'No'
                    else:
                        first.misc['SpaceAfter'] = ''
                    hyph.remove()
                    node.remove()
                # We cannot be sure whether the original annotation correctly said that there are no spaces around the hyphen.
                # If it did not, then we have a mismatch with the sentence text, which we must fix.
                # The following will also fix cases where there was an n-dash ('–') instead of a hyphen ('-').
                root.text = root.compute_text()
        # In some cases the non-/sub-/anti- prefix is annotated as the head of the phrase and the above pattern does not catch it.
        elif first.ord == node.ord+2 and re.match(r'^(non|sub|anti|multi|kontra)$', node.form.lower()):
            prefix = node
            stem = first # here it is not the first part at all
            hyph = stem.prev_node
            if hyph.is_descendant_of(first) and re.match(r'^(-|–|--)$', hyph.form):
                # For the non-/sub-/anti- prefix we want to take the morphology from the second word.
                stem.lemma = prefix.lemma + '-' + stem.lemma
                stem.misc['MorphInd'] = re.sub(r'\$\+\^', '+', prefix.misc['MorphInd'] + '+' + stem.misc['MorphInd'])
                # Neither the hyphen nor the prefix should have children.
                # If they do, re-attach the children to the stem.
                for c in hyph.children:
                    c.parent = stem
                for c in prefix.children:
                    c.parent = stem
                # Merge the three nodes.
                # It is possible that the last token of the original annotation
                # is included in a multi-word token. Then we must extend the
                # multi-word token to the whole reduplication! Example:
                # pemeran-pemerannya (the actors) ... originally 'pemeran' and '-'
                # are tokens, 'pemerannya' is a MWT split to 'pemeran' and 'nya'.
                mwt = stem.multiword_token
                if mwt:
                    # We assume that the MWT has only two words. We are not prepared for other possibilities.
                    if len(mwt.words) > 2:
                        logging.critical('MWT of only two words is expected')
                    mwtmisc = mwt.misc.copy()
                    second = mwt.words[1]
                    mwt.remove()
                    stem.form = prefix.form + '-' + stem.form
                    prefix.remove()
                    hyph.remove()
                    stem.misc['SpaceAfter'] = ''
                    mwt = root.create_multiword_token([stem, second], stem.form + second.form, mwtmisc)
                else:
                    stem.form = prefix.form + '-' + stem.form
                    prefix.remove()
                    hyph.remove()
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

    def lemmatize_from_morphind(self, node):
        # The MISC column contains the output of MorphInd for the current word.
        # The analysis has been interpreted wrongly for some verbs, so we need
        # to re-interpret it and extract the correct lemma.
        morphind = node.misc['MorphInd']
        if node.upos == 'VERB':
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
        elif node.upos == 'NOUN':
            if morphind:
                # Remove the start and end tags from morphind.
                morphind = re.sub(r"^\^", "", morphind)
                morphind = re.sub(r"\$$", "", morphind)
                # Remove the final XPOS tag from morphind.
                morphind = re.sub(r'_(N[SP]D|VSA)$', '', morphind)
                # Do not proceed if there is an unexpected final XPOS tag.
                if not re.search(r'_[A-Z][-A-Z][-A-Z]$', morphind):
                    # Split morphind to prefix, stem, and suffix.
                    morphemes = re.split(r'\+', morphind)
                    # Expected prefixes are peN-, per-, ke-, ber-.
                    # Expected suffix is -an.
                    if len(morphemes) > 1 and re.match(r'^an$', morphemes[-1]):
                        del morphemes[-1]
                    if len(morphemes) > 1 and re.match(r'^(peN|per|ke|ber)$', morphemes[0]):
                        del morphemes[0]
                    # Check that we are left with just one morpheme.
                    if len(morphemes) != 1:
                        logging.warning("One morpheme expected, found %d %s, morphind = '%s', form = '%s', feats = '%s'" % (len(morphemes), morphemes, morphind, node.form, node.feats))
                    else:
                        lemma = morphemes[0]
                        # Remove the stem POS category.
                        lemma = re.sub(r'<[a-z]+>', '', lemma)
                        node.lemma = lemma
        elif node.upos == 'ADJ':
            if morphind:
                # Remove the start and end tags from morphind.
                morphind = re.sub(r"^\^", "", morphind)
                morphind = re.sub(r"\$$", "", morphind)
                # Remove the final XPOS tag from morphind.
                morphind = re.sub(r'_ASS$', '', morphind)
                # Do not proceed if there is an unexpected final XPOS tag.
                if not re.search(r'_[A-Z][-A-Z][-A-Z]$', morphind):
                    # Split morphind to prefix, stem, and suffix.
                    morphemes = re.split(r'\+', morphind)
                    # Expected prefix is ter-.
                    if len(morphemes) > 1 and re.match(r'^ter$', morphemes[0]):
                        del morphemes[0]
                    # Check that we are left with just one morpheme.
                    if len(morphemes) != 1:
                        logging.warning("One morpheme expected, found %d %s, morphind = '%s', form = '%s', feats = '%s'" % (len(morphemes), morphemes, morphind, node.form, node.feats))
                    else:
                        lemma = morphemes[0]
                        # Remove the stem POS category.
                        lemma = re.sub(r'<[a-z]+>', '', lemma)
                        node.lemma = lemma
            else:
                logging.warning("No MorphInd analysis found for form '%s'" % (node.form))

    def process_node(self, node):
        self.fix_plural_propn(node)
        self.fix_upos_based_on_morphind(node)
        self.fix_semua(node)
        self.rejoin_ordinal_numerals(node)
        self.fix_ordinal_numerals(node)
        self.rejoin_decades(node)
        self.merge_reduplication(node)
        self.fix_satu_satunya(node)
        self.lemmatize_from_morphind(node)
