"""Block SetSpaceAfter for heuristic setting of SpaceAfter=No.

Usage:
udapy -s ud.SetSpaceAfter < in.conllu > fixed.conllu

Author: Martin Popel
"""
import collections

from udapi.core.block import Block


class SetSpaceAfter(Block):
    """Block for heuristic setting of the SpaceAfter=No MISC attribute."""

    def __init__(self, not_after='¡ ¿ ( [ { „ /', not_before='. , ; : ! ? } ] ) / ?? ??? !! !!! ... …',
                 fix_text=True, extra_not_after='', extra_not_before='', **kwargs):
        super().__init__(**kwargs)
        self.not_after = (not_after + ' ' + extra_not_after).split(' ')
        self.not_before = (not_before + ' ' + extra_not_before).split(' ')
        self.fix_text = fix_text
        self.changed = False

    def process_tree(self, root):
        nodes = root.descendants
        count_of_form = collections.Counter([n.form for n in nodes])
        self.changed = False

        # Undirected double quotes are ambiguous.
        # If there is an even number of quotes in a sentence, suppose they are not nested
        # and treat odd-indexed ones as opening and even-indexed ones as closing.
        # Otherwise (odd number, e.g. when quoting multiple sentences), don't remove any space.
        matching_quotes = not bool(count_of_form['"'] % 2)
        not_after, not_before = self.not_after, self.not_before
        odd_indexed_quote = True

        # Some languages use directed „quotes“ and some “quotes”,
        # so the symbol “ (U+201C) is ambiguous and we heuristically check for presence of „.
        if count_of_form['„']:
            not_before += ['“']
        else:
            not_after += ['“']

        for i, node in enumerate(nodes[:-1]):
            next_form = nodes[i + 1].form
            if node.form in self.not_after or next_form in not_before:
                self.mark_no_space(node)
            if node.form == '"':
                if matching_quotes:
                    if odd_indexed_quote:
                        self.mark_no_space(node)
                    elif i:
                        self.mark_no_space(nodes[i - 1])
                    odd_indexed_quote = not odd_indexed_quote
                elif i==0:
                    self.mark_no_space(node)

        if nodes[-1].form == '"':
            self.mark_no_space(nodes[-2])

        if self.fix_text and self.changed:
            root.text = root.compute_text()

    def mark_no_space(self, node):
        """Mark a node with SpaceAfter=No unless it is a goeswith exception."""
        if not self.is_goeswith_exception(node):
            mwt = node.multiword_token
            if mwt:
                if mwt.words[-1] == node:
                    mwt.misc['SpaceAfter'] = 'No'
                    self.changed = True
            else:
                node.misc['SpaceAfter'] = 'No'
                self.changed = True

    @staticmethod
    def is_goeswith_exception(node):
        """Is this node excepted from SpaceAfter=No because of the `goeswith` deprel?

        Deprel=goeswith means that a space was (incorrectly) present in the original text,
        so we should not add SpaceAfter=No in these cases.
        We expect valid annotation of goeswith (no gaps, first token as head).
        """
        return node.next_node.deprel == 'goeswith'
