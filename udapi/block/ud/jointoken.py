"""
Block ud.JoinToken will join a given token with the preceding one.
"""
from udapi.core.block import Block
import logging


class JoinToken(Block):
    """
    Merge two tokens into one. A MISC attribute is used to mark the tokens that
    should join the preceding token. (The attribute may have been set by an
    annotator or by a previous block that tests the specific conditions under
    which joining is desired.) Joining cannot be done across sentence
    boundaries; if necessary, apply util.JoinSentence first. Multiword tokens
    are currently supported only partially: If the token consists of the
    current and the previous node only, they will be replaced by a node
    representing the surface token. Any other situation involving a MWT will
    be rejected. (The block ud.JoinAsMwt may be of some help, but it works differently.)
    Merging is simple if there is no space between the tokens (see SpaceAfter=No
    at the first token). If there is a space, there are three options in theory:

        1. Keep the tokens as two nodes but apply the UD goeswith relation
           (see https://universaldependencies.org/u/overview/typos.html) and
           the related annotation rules.
        2. Join them into one token that contains a space. Such "words with
           spaces" can be exceptionally allowed in UD if they are registered
           in the given language.
        3. Remove the space without any trace. Not recommended in UD unless the
           underlying text was created directly for UD and can be thus considered
           part of the annotation.

    At present, this block does not support merging with spaces at all, but
    in the future one or more of the options may be added.
    """

    def __init__(self, misc_name='JoinToken', misc_value=None, **kwargs):
        """
        Args:
        misc_name: name of the MISC attribute that can trigger the joining
            default: JoinToken
        misc_value: value of the MISC attribute to trigger the joining;
            if not specified, then simple occurrence of the attribute with any value will cause the joining
            MISC attributes that have triggered sentence joining will be removed from their node.
        """
        super().__init__(**kwargs)
        self.misc_name = misc_name
        self.misc_value = misc_value

    def process_node(self, node):
        """
        The JoinToken (or equivalent) attribute in MISC will trigger action.
        Either the current node will be merged with the previous node and the
        attribute will be removed from MISC, or a warning will be issued that
        the merging cannot be done and the attribute will stay in MISC. Note
        that multiword token lines and empty nodes are not even scanned for
        the attribute, so if it is there, it will stay there but no warning
        will be printed.
        """
        if node.misc[self.misc_name] == '':
            return
        if self.misc_value and node.misc[self.misc_name] != self.misc_value:
            return
        prevnode = node.prev_node
        if not prevnode:
            logging.warning("MISC %s cannot be used at the first token of a sentence." % self.misc_name)
            node.misc['Bug'] = 'JoiningTokenNotSupportedHere'
            return
        ###!!! Only limited support for MWT: If there are two words and this is the second one, the MWT will become single word-token again.
        ###!!! Other configurations with MWT will not be processed and a warning will be issued.
        if node.multiword_token and prevnode.multiword_token and node.multiword_token == prevnode.multiword_token and len(node.multiword_token.words) == 2:
            mwt = node.multiword_token
            # Adjust the attributes of the nodes so that the code below
            # that joins two standard nodes will do what is needed.
            prevnode.form = mwt.form
            prevnode.misc['SpaceAfter'] = 'No'
            node.form = ''
            node.misc['SpaceAfter'] = mwt.misc['SpaceAfter']
            mwt.remove()
        elif node.multiword_token or prevnode.multiword_token:
            logging.warning("MISC %s cannot be used if one of the nodes belongs to a multiword token." % self.misc_name)
            node.misc['Bug'] = 'JoiningTokenNotSupportedHere'
            return
        if prevnode.misc['SpaceAfter'] != 'No':
            logging.warning("MISC %s cannot be used if there is space between the tokens." % self.misc_name)
            node.misc['Bug'] = 'JoiningTokensWithSpaceNotSupported'
            return
        ###!!! This block currently must not be applied on data containing
        ###!!! enhanced dependencies. We must first implement adjustments of
        ###!!! the enhanced structure.
        if prevnode.deps or node.deps:
            logging.fatal('At present this block cannot be applied to data with enhanced dependencies.')
        # If the first token depends on the second token, re-attach it to the
        # second token's parent to prevent cycles.
        if prevnode in node.descendants:
            prevnode.parent = node.parent
            prevnode.deprel = node.deprel
        # Re-attach all children of the second token to the first token.
        for c in node.children:
            c.parent = prevnode
        # Concatenate the word forms of the two tokens. Assume that morphological
        # annotation, including the lemma, is already updated accordingly (we
        # cannot guess it anyway).
        prevnode.form += node.form
        # Remove SpaceAfter=No from the first token unless the second token has
        # this attribute, too (meaning that there is no space between the second
        # token and whatever comes next).
        prevnode.misc['SpaceAfter'] = node.misc['SpaceAfter']
        # Remove the current node. The joining instruction was in its MISC, so
        # it will disappear together with the node.
        node.remove()
