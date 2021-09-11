"""Block to fix annotation of UD Indonesian-GSD."""
from udapi.core.block import Block
import logging
import re

class FixGSD(Block):

    def lemmatize_verb_from_morphind(self, node):
        # The MISC column contains the output of MorphInd for the current word.
        # The analysis has been interpreted wrongly for some verbs, so we need
        # to re-interpret it and extract the correct lemma.
        if node.upos == "VERB":
            morphind = node.misc["MorphInd"]
            # Remove the start and end tags from morphind.
            morphind = re.sub(r"^\^", "", morphind)
            morphind = re.sub(r"\$$", "", morphind)
            # Remove the final XPOS tag from morphind.
            morphind = re.sub(r"_VS[AP]$", "", morphind)
            # Split morphind to prefix, stem, and suffix.
            morphemes = re.split(r"\+", morphind)
            # Expected suffixes are -kan, -i, -an, or no suffix at all.
            if len(morphemes) > 1 and re.match(r"^(kan|i|an)$", morphemes[-1]):
                del morphemes[-1]
            # Expected prefixes are meN-, di-, ber-, peN-, ke-, ter-, se-, or no prefix at all.
            # There can be two prefixes in a row, e.g., "ber+ke+", or "ter+peN+".
            while len(morphemes) > 1 and re.match(r"^(meN|di|ber|peN|ke|ter|se|per)$", morphemes[0]):
                del morphemes[0]
            # Check that we are left with just one morpheme.
            if len(morphemes) != 1:
                logging.warning("One morpheme expected, found %d %s, morphind = '%s'" % (len(morphemes), morphemes, morphind))
            else:
                lemma = morphemes[0]
                # Remove the stem POS category.
                lemma = re.sub(r"<[a-z]+>$", "", lemma)
                node.lemma = lemma

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

    def process_node(self, node):
        self.lemmatize_verb_from_morphind(node)
