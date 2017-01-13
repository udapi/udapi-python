import re

from udapi.core.basereader import BaseReader
from udapi.core.root import Root

# Compile a set of regular expressions that will be searched over the lines.
# The equal sign after sent_id was added to the specification in UD v2.0.
# This reader accepts also older-style sent_id (until UD v2.0 treebanks are released).
RE_SENT_ID = re.compile(r'^# sent_id\s*=?\s*(\S+)')
RE_TEXT = re.compile(r'^# text\s*=\s*(.+)')

class Conllu(BaseReader):
    """A reader of the CoNLL-U files."""

    def __init__(self, strict=False, **kwargs):
        super().__init__(**kwargs)

        # A list of Conllu columns.
        self.node_attributes = ["ord", "form", "lemma", "upos", "xpos",
                                "feats", "head", "deprel", "deps", "misc"]

        # TODO: this should be invoked from the parent class
        self.finished = False

        # Strict.
        self.strict = strict
        if strict in [1, '1', 'True', 'true']:
            self.strict = True

        # Remember total number of bundles
        self.total_number_of_bundles = 0

    def read_tree(self, document=None):
        root = Root()
        nodes = [root]
        parents = [0]
        comment = ''
        filehandle = self.filehandle()
        if filehandle is None:
            return None

        mwts = []
        for line in filehandle:
            line = line.rstrip()
            if line == '':
                break
            if line[0] == '#':
                sent_id_match = RE_SENT_ID.search(line)
                if sent_id_match is not None:
                    root.sent_id = sent_id_match.group(1)
                else:
                    text_match = RE_TEXT.search(line)
                    if text_match is not None:
                        root.text = text_match.group(1)
                    else:
                        comment = comment + line[1:] + "\n"
            else:
                fields = line.split('\t')
                if self.strict and len(fields) != len(self.node_attributes):
                    raise RuntimeError('Wrong number of columns in %r' % line)
                # multi-word tokens will be processed later
                if fields[0].find('-') != -1:
                    mwts.append(fields)
                    continue

                node = root.create_child()

                # TODO slow implementation of speed-critical loading
                for (n_attribute, attribute_name) in enumerate(self.node_attributes):
                    if attribute_name == 'head':
                        parents.append(int(fields[n_attribute]))
                    elif attribute_name == 'ord':
                        setattr(node, 'ord', int(fields[n_attribute]))
                    elif attribute_name == 'deps':
                        setattr(node, 'raw_deps', fields[n_attribute])
                    else:
                        setattr(node, attribute_name, fields[n_attribute])

                nodes.append(node)

        # If no nodes were read from the filehandle (so only root remained in nodes),
        # we return None as a sign of failure (end of file or more than one empty line).
        if len(nodes) == 1:
            return None

        # Empty sentences are not allowed in CoNLL-U,
        # but if the users want to save just the sentence string and/or sent_id
        # they need to create one artificial node and mark it with Empty=Yes.
        # In that case, we will delete this node, so the tree will have just the (technical) root.
        # See also udapi.block.write.Conllu, which is compatible with this trick.
        if len(nodes) == 2 and nodes[1].misc == 'Empty=Yes':
            nodes.pop()

        # Set dependency parents (now, all nodes of the tree are created).
        for node_ord, node in enumerate(nodes[1:], 1):
            node.parent = nodes[parents[node_ord]]

        # Set root attributes (descendants for faster iteration of all nodes in a tree).
        root._descendants = nodes[1:]

        if comment != '':
            root.misc = comment

        # Create multi-word tokens.
        for fields in mwts:
            range_start, range_end = fields[0].split('-')
            words = nodes[int(range_start):int(range_end)+1]
            mwt = root.create_multiword_token(words, form=fields[1])
            if fields[-1] != '_':
                mwt.misc = fields[-1]

        return root
