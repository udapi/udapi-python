"""
Block ud.SplitToken will split a given token into multiple tokens.
"""
from udapi.core.block import Block
import re
import logging


class SplitToken(Block):
    """
    Split a token into two or more. A MISC attribute is used to mark the tokens
    that should be split. (The attribute may have been set by an annotator or
    by a previous block that tests the specific conditions under which splitting
    is desired.) Multiword tokens are currently not supported: The node to be
    split cannot belong to a MWT. Note that the result will not be a MWT either
    (use the block ud.AddMwt if that is desired). There will be simply a new
    attribute SpaceAfter=No, possibly accompanied by CorrectSpaceAfter=Yes
    (indicating that this was an error in the source text).
    """

    def __init__(self, misc_name='SplitToken', **kwargs):
        """
        Args:
        misc_name: name of the MISC attribute that can trigger the splitting
            default: SplitToken
            The value of the attribute should indicate where to split the token.
            It should be a string that is identical to node.form except that
            there is one or more spaces where the token should be split.
        """
        super().__init__(**kwargs)
        self.misc_name = misc_name

    def process_node(self, node):
        """
        The SplitToken (or equivalent) attribute in MISC will trigger action.
        Either the current node will be split to multiple nodes and the
        attribute will be removed from MISC, or a warning will be issued that
        the splitting cannot be done and the attribute will stay in MISC. Note
        that multiword token lines and empty nodes are not even scanned for
        the attribute, so if it is there, it will stay there but no warning
        will be printed.
        """
        value = node.misc[self.misc_name]
        if value == '':
            return
        if node.multiword_token:
            logging.warning(f"MISC {self.misc_name} cannot be used if the node belongs to a multiword token.")
            node.misc['Bug'] = 'SplittingTokenNotSupportedHere'
            return
        ###!!! This block currently must not be applied on data containing
        ###!!! enhanced dependencies. We must first implement adjustments of
        ###!!! the enhanced structure.
        if node.deps:
            logging.fatal('At present this block cannot be applied to data with enhanced dependencies.')
        # Verify that the value of the MISC attribute can be used as specification
        # of the split.
        if re.match(r'^\s', value) or re.search(r'\s$', value) or re.search(r'\s\s', value):
            logging.warning(f"MISC {self.misc_name} is '{value}'; leading spaces, trailing spaces or multiple consecutive spaces are not allowed.")
            node.misc['Bug'] = f'{self.misc_name}BadValue'
            return
        if re.search(r'\s', node.form):
            logging.warning(f"MISC {self.misc_name} cannot be used with nodes whose forms contain a space (here '{node.form}').")
            node.misc['Bug'] = 'SplittingTokenNotSupportedHere'
            return
        if re.sub(r' ', '', value) != node.form:
            logging.warning(f"MISC {self.misc_name} value '{value}' does not match the word form '{node.form}'.")
            node.misc['Bug'] = f'{self.misc_name}BadValue'
            return
        # Do the split.
        space_after = node.misc['SpaceAfter']
        forms = value.split(' ')
        # Optionally, SplitTokenMorpho in MISC can have the morphological annotation
        # of the new tokens. For example:
        # SplitTokenMorpho=LEMMA=popisovat\tUPOS=VERB\tFEATS=Aspect=Imp\\pMood=Ind\\pNumber=Sing\\pPerson=3\\pPolarity=Pos\\pTense=Pres\\pVerbForm=Fin\\pVoice=Act
        if node.misc['SplitTokenMorpho'] != '':
            morphoblocks = [''] + node.misc['SplitTokenMorpho'].split(' ')
            del node.misc['SplitTokenMorpho']
        else:
            morphoblocks = ['' for x in forms]
        node.form = forms[0]
        last_node = node
        for form, morpho in zip(forms[1:], morphoblocks[1:]):
            last_node.misc['SpaceAfter'] = 'No'
            last_node.misc['CorrectSpaceAfter'] = 'Yes'
            lemma = form
            upos = node.upos
            feats = str(node.feats)
            xpos = node.xpos
            if morpho != '':
                cols = morpho.split('\\t')
                for c in cols:
                    colname, value = c.split('=', 1)
                    if colname == 'LEMMA':
                        lemma = value
                    elif colname == 'UPOS':
                        upos = value
                    elif colname == 'FEATS':
                        feats = re.sub(r'\\p', '|', value)
                    elif colname == 'XPOS':
                        xpos = value
                    else:
                        logging.fatal(f"c = {c}")
            new_node = node.create_child(form=form, lemma=lemma, upos=upos, feats=feats, xpos=xpos, deprel='dep')
            new_node.shift_after_node(last_node)
            last_node = new_node
        last_node.misc['SpaceAfter'] = space_after
        del node.misc[self.misc_name]
