"""Block that takes PARSEME-like annotation of multiword expressions from MISC
   and normalizes it so that the type is always annotated at the first word of
   the expression."""
from udapi.core.block import Block
import logging
import re

class Normalize(Block):

    def collect_mwes(self, root):
        """
        Collects annotations of multiword expressions from MISC of the nodes.
        The expected annotation is in the style of Parseme (see
        https://gitlab.com/parseme/corpora/-/wikis/home#annotation and download
        the data from http://hdl.handle.net/11372/LRT-5124), except that there
        are only ten columns and the annotation from the eleventh column is
        copied to the tenth (MISC) as the attribute Mwe (e.g., Mwe=1:LVC.cause).
        """
        nodes = root.descendants
        mwes = {} # for each mwe id, its type and list of node ids
        mwes_by_nodes = {} # for each node id, a list of mwe ids
        for n in nodes:
            mwes_by_nodes[n.ord] = []
            miscmwe = n.misc['Mwe']
            if miscmwe:
                # A node may belong to multiple multiword expressions.
                miscmwes = miscmwe.split(';')
                for m in miscmwes:
                    # Either it is NUMBER:TYPE, or just NUMBER.
                    # Number identifies this MWE among all MWEs in the sentence.
                    # Type is a main uppercase string (VID, LVC etc.), optionally
                    # followed by a subtype ('LVC.cause').
                    # See https://gitlab.com/parseme/corpora/-/wikis/home
                    match = re.match(r"^([0-9]+)(?::([A-Za-z\.]+))?$", m)
                    if match:
                        number = match.group(1)
                        type = match.group(2)
                        if not number in mwes:
                            mwes[number] = {'nodes': [], 'type': ''}
                        if type:
                            mwes[number]['type'] = type
                        mwes[number]['nodes'].append(n.ord)
                        mwes_by_nodes[n.ord].append(number)
                    else:
                        logging.warning("Cannot parse Mwe=%s" % m)
        return (mwes, mwes_by_nodes)

    def process_tree(self, root):
        """
        Collects annotations of multiword expressions from MISC of the nodes.
        Then saves them back but makes sure that the type is annotated at the
        first word of the expression (as opposed to the syntactic head or to
        any other word).
        """
        (mwes, mwes_by_nodes) = self.collect_mwes(root)
        nodes = root.descendants
        for n in nodes:
            # Erase the previous MWE annotations so we can start from scratch.
            n.misc['Mwe'] = ''
            # There may be multiple MWEs this node is member of.
            annotations = []
            for m in mwes_by_nodes[n.ord]:
                if n.ord == mwes[m]['nodes'][0]:
                    annotations.append("%s:%s" % (m, mwes[m]['type']))
                else:
                    annotations.append(m)
            if annotations:
                n.misc['Mwe'] = ';'.join(annotations)
