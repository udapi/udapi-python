""""Conll is a reader block for CoNLL-like files (CoNLL-U, CoNLL-X, CoNLL-2009)."""
import json
import logging
import re

import udapi.block.read.conllu
from udapi.core.root import Root
from udapi.core.node import Node


class Conll(udapi.block.read.conllu.Conllu):
    """A reader of the CoNLL-U files."""

    def __init__(self, separator='tab',
                 attributes='ord,form,lemma,upos,xpos,feats,head,deprel,deps,misc', **kwargs):
        """Create the Conll reader object.

        This us a subclass of udapi.block.read.conllu.Conllu,
        which adds a support for arbitrary column names and thus supporting not only CoNLL-U,
        but also CoNLL-X, CoNLL-2009 and many other CoNLL-like formats.

        Args:
        separator: How are the columns separated?
            Default='tab' is the only possibility in valid CoNLL-U files.
            'space' means one or more whitespaces (this does not allow forms with space).
            'doublespace' means two or more spaces.
        attributes: comma-separated list of column names in the input files
            (default='ord,form,lemma,upos,xpos,feats,head,deprel,deps,misc')
            Changing the default can be used for loading CoNLL-like formats (not valid CoNLL-U).
            For ignoring a column, use "_" as its name.
            Column "ord" marks the column with 1-based word-order number/index (usualy called ID).
            Column "head" marks the column with dependency parent index (word-order number).

            For example, for CoNLL-X which uses name1=value1|name2=value2 format of FEATS, use
            `attributes=ord,form,lemma,upos,xpos,feats,head,deprel,_,_`
            but note that attributes upos, feats and deprel will contain language-specific values,
            not valid according to UD guidelines and a further conversion will be needed.
            You will loose the projective_HEAD and projective_DEPREL attributes.

            For CoNLL-2009 you can use `attributes=ord,form,lemma,_,upos,_,feats,_,head,_,deprel`.
            You will loose the predicted_* attributes and semantic/predicate annotation.

            TODO: allow storing the rest of columns in misc, e.g. `node.misc[feats]`
            for feats which do not use the name1=value1|name2=value2 format.
        """
        super().__init__(**kwargs)
        self.node_attributes = attributes.split(',')
        self.separator = separator

    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    # Maybe the code could be refactored, but it is speed-critical,
    # so benchmarking is needed because calling extra methods may result in slowdown.

    def parse_node_line(self, line, root, nodes, parents, mwts):
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
            return
        if '.' in fields[0]:
            empty = root.create_empty_child(form=fields[1], lemma=fields[2], upos=fields[3],
                                            xpos=fields[4], feats=fields[5], misc=fields[9])
            empty.ord = fields[0]
            empty.raw_deps = fields[8]  # TODO
            return

        # This implementation is slower than in read.Conllu,
        # but it allows for arbitrary columns
        node = root.create_child()
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
            elif attribute_name != '_' and fields[n_attribute] != '_':
                setattr(node, attribute_name, fields[n_attribute])

        nodes.append(node)

    # Acknowledged code duplication with read.Conllu
    def read_tree_from_lines(self, lines):
        root = Root()
        nodes = [root]
        parents = [0]
        mwts = []
        for line in lines:
            if line[0] == '#':
                self.parse_comment_line(line, root)
            else:
                self.parse_node_line(line, root, nodes, parents, mwts)

        # If no nodes were read from the filehandle (so only root remained in nodes),
        # we return None as a sign of failure (end of file or more than one empty line).
        if len(nodes) == 1:
            return None

        # Empty sentences are not allowed in CoNLL-U,
        # but if the users want to save just the sentence string and/or sent_id
        # they need to create one artificial node and mark it with Empty=Yes.
        # In that case, we will delete this node, so the tree will have just the (technical) root.
        # See also udapi.block.write.Conllu, which is compatible with this trick.
        if len(nodes) == 2 and str(nodes[1].misc) == 'Empty=Yes':
            nodes.pop()
            root._children = []
            root._descendants = []

        # Set dependency parents (now, all nodes of the tree are created).
        for node_ord, node in enumerate(nodes[1:], 1):
            try:
                parent = nodes[parents[node_ord]]
            except IndexError:
                raise ValueError("Node %s HEAD is out of range (%d)" % (node, parents[node_ord]))
            if node is parent:
                if self.fix_cycles:
                    logging.warning("Ignoring a cycle (attaching to the root instead):\n%s", node)
                    node._parent = root
                    root._children.append(node)
                else:
                    raise ValueError(f"Detected a cycle: {node} attached to itself")
            elif node.children:
                climbing = parent._parent
                while climbing:
                    if climbing is node:
                        if self.fix_cycles:
                            logging.warning("Ignoring a cycle (attaching to the root instead):\n%s", parent)
                            parent = root
                            break
                        else:
                            raise ValueError(f"Detected a cycle: {node}")
                    climbing = climbing._parent
            node._parent = parent
            parent._children.append(node)

        # Create multi-word tokens.
        for fields in mwts:
            range_start, range_end = fields[0].split('-')
            words = nodes[int(range_start):int(range_end) + 1]
            root.create_multiword_token(words, form=fields[1], misc=fields[-1])

        return root
