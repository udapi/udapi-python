"""Block SetSpaceAfterFromText for setting of SpaceAfter=No according to the sentence text.

Usage:
udapy -s ud.SetSpaceAfterFromText < in.conllu > fixed.conllu

Author: Martin Popel
"""
import logging

from udapi.core.block import Block


class SetSpaceAfterFromText(Block):
    """Block for setting of the SpaceAfter=No MISC attribute according to the sentence text."""

    def process_tree(self, root):
        text = root.text
        if text is None:
            raise ValueError('Tree %s has no text, cannot use ud.SetSpaceAfterFromText' % root)
        if text == root.compute_text():
            return

        for node in root.token_descendants:
            if text.startswith(node.form):
                text = text[len(node.form):]
                if not text or text[0].isspace():
                    del node.misc['SpaceAfter']
                    text = text.lstrip()
                else:
                    node.misc['SpaceAfter'] = 'No'
            else:
                logging.warning('Node %s does not match text "%s"', node, text[:20])
                return
        if text:
            logging.warning('Extra text "%s" in tree %s', text, root)
