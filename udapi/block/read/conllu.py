""""Conllu is a reader block for the CoNLL-U files."""
import json
import logging
import re

from udapi.core.basereader import BaseReader
from udapi.core.root import Root

# Compile a set of regular expressions that will be searched over the lines.
# The equal sign after sent_id was added to the specification in UD v2.0.
# This reader accepts also older-style sent_id (until UD v2.0 treebanks are released).
RE_SENT_ID = re.compile(r'^# sent_id\s*=?\s*(\S+)')
RE_TEXT = re.compile(r'^# text\s*=\s*(.+)')
RE_NEWPARDOC = re.compile(r'^# (newpar|newdoc) (?:\s*id\s*=\s*(.+))?')
RE_JSON = re.compile(r'^# (doc_)?json_([^ =]+)\s*=\s*(.+)')


class Conllu(BaseReader):
    """A reader of the CoNLL-U files."""

    def __init__(self, strict=False, separator='tab', empty_parent='warn',
                 attributes='ord,form,lemma,upos,xpos,feats,head,deprel,deps,misc', **kwargs):
        """Create the Conllu reader object.

        Args:
        strict: raise an exception if errors found (default=False, i.e. a robust mode)
        separator: How are the columns separated?
            Default='tab' is the only possibility in valid CoNLL-U files.
            'space' means one or more whitespaces (this does not allow forms with space).
            'doublespace' means two or more spaces.
        empty_parent: What to do if HEAD is _? Default=warn - issue a warning and attach to the root
            or if strict=1 issue an exception. With `empty_parent=ignore` no warning is issued.
        attributes: comma-separated list of column names in the input files
            (default='ord,form,lemma,upos,xpos,feats,head,deprel,deps,misc')
            Changing the default can be used for loading CoNLL-like formats (not valid CoNLL-U).
            For ignoring a column, use "_" as its name.
            Column "ord" marks the column with 1-based word-order number/index (usualy called ID).
            Column "head" marks the column with dependency parent index (word-order number).

            For example, for CoNLL-X which uses name1=value1|name2=value2 format of FEATS, use
            `attributes=ord,form,lemma,upos,xpos,feats,head,deprel,_,_`
            but note attributes that upos, feats and deprel will contain language-specific values,
            not valid according to UD guidelines and a further conversion will be needed.
            You will loose the projective_HEAD and projective_DEPREL attributes.

            For CoNLL-2009 you can use `attributes=ord,form,lemma,_,upos,_,feats,_,head,_,deprel`.
            You will loose the predicted_* attributes and semantic/predicate annotation.

            TODO: allow storing the rest of columns in misc, e.g. `node.misc[feats]`
            for feats which do not use the name1=value1|name2=value2 format.
        """
        super().__init__(**kwargs)
        self.node_attributes = attributes.split(',')
        self.strict = strict
        self.separator = separator
        self.empty_parent = empty_parent

    @staticmethod
    def parse_comment_line(line, root, document):
        """Parse one line of CoNLL-U and fill sent_id, text, newpar, newdoc in root."""
        sent_id_match = RE_SENT_ID.match(line)
        if sent_id_match is not None:
            root.sent_id = sent_id_match.group(1)
            return

        text_match = RE_TEXT.match(line)
        if text_match is not None:
            root.text = text_match.group(1)
            return

        pardoc_match = RE_NEWPARDOC.match(line)
        if pardoc_match is not None:
            value = True if pardoc_match.group(2) is None else pardoc_match.group(2)
            if pardoc_match.group(1) == 'newpar':
                root.newpar = value
            else:
                root.newdoc = value
            return

        json_match = RE_JSON.match(line)
        if json_match is not None:
            container = document if json_match.group(1) == 'doc_' else root
            container.json[json_match.group(2)] = json.loads(json_match.group(3))
            return

        root.comment += line[1:] + "\n"

    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    # Maybe the code could be refactored, but it is speed-critical,
    # so benchmarking is needed because calling extra methods may result in slowdown.
    def read_tree(self, document=None):
        if self.filehandle is None:
            return None

        root = Root()
        nodes = [root]
        parents = [0]
        mwts = []
        for line in self.filehandle:
            line = line.rstrip()
            if line == '':
                break
            if line[0] == '#':
                self.parse_comment_line(line, root, document)
            else:
                if self.separator == 'tab':
                    fields = line.split('\t')
                elif self.separator == 'space':
                    fields = line.split()
                elif self.separator == 'doublespace':
                    fields = re.split('  +', line)
                else:
                    raise ValueError('separator=%s is not valid' % self.separator)
                if len(fields) != len(self.node_attributes):
                    if self.strict:
                        raise RuntimeError('Wrong number of columns in %r' % line)
                    fields.extend(['_'] * (len(self.node_attributes) - len(fields)))
                # multi-word tokens will be processed later
                if '-' in fields[0]:
                    mwts.append(fields)
                    continue
                if '.' in fields[0]:
                    empty = root.create_empty_child(form=fields[1], lemma=fields[2], upos=fields[3],
                                                    xpos=fields[4], feats=fields[5], misc=fields[9])
                    empty.ord = fields[0]
                    empty.raw_deps = fields[8]  # TODO
                    continue

                node = root.create_child()

                # TODO slow implementation of speed-critical loading
                for (n_attribute, attribute_name) in enumerate(self.node_attributes):
                    if attribute_name == 'head':
                        try:
                            parents.append(int(fields[n_attribute]))
                        except ValueError as exception:
                            if not self.strict and fields[n_attribute] == '_':
                                if self.empty_parent == 'warn':
                                    logging.warning("Empty parent/head index in '%s'", line)
                                parents.append(0)
                            else:
                                raise exception
                    elif attribute_name == 'ord':
                        setattr(node, 'ord', int(fields[n_attribute]))
                    elif attribute_name == 'deps':
                        setattr(node, 'raw_deps', fields[n_attribute])
                    elif attribute_name != '_':
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
        # TODO: parent setter checks for cycles, but this is something like O(n*log n)
        # if done for each node. It could be done faster if the whole tree is checked at once.
        # Also parent setter removes the node from its old parent's list of children,
        # this could be skipped here by not using `node = root.create_child()`.
        for node_ord, node in enumerate(nodes[1:], 1):
            try:
                node.parent = nodes[parents[node_ord]]
            except IndexError:
                raise ValueError("Node %s HEAD is out of range (%d)" % (node, parents[node_ord]))

        # Create multi-word tokens.
        for fields in mwts:
            range_start, range_end = fields[0].split('-')
            words = nodes[int(range_start):int(range_end) + 1]
            root.create_multiword_token(words, form=fields[1], misc=fields[-1])

        return root
