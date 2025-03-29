""""Conllup is a reader block for the CoNLL-UPlus format.

Columns which don't have standardize attributes in Udapi/CoNLL-U
are stored in MISC (as key=value pairs).
"""
import json
import logging
import re

import udapi.block.read.conll
from udapi.core.root import Root
from udapi.core.node import Node

RE_GLOBAL_COLUMNS = re.compile(r'^# global.columns\s*=\s*(.+)')
COLUMN_MAP = {
    'ID': 'ord',
}
NORMAL_ATTRS = 'form lemma upos xpos feats deprel misc'.split()

class Conllup(udapi.block.read.conll.Conll):
    """A reader of the CoNLL-UPlus files."""

    def __init__(self, attributes='autodetect', **kwargs):
        """Create the Conllup reader object.

        Args:
        attributes: comma-separated list of column names in the input files
            (can be used if the global.columns header is missing or needs to be overriden).
            Default='autodetect' which means the column names will be loaded from the global.columns header.
            For ignoring a column, use "_" as its name.
        """
        super().__init__(**kwargs)
        if attributes == 'autodetect':
            self.node_attributes = None
        else:
            self.node_attributes = attributes.split(',')

    def parse_comment_line(self, line, root):
        if self.node_attributes is None:
            global_columns_match = RE_GLOBAL_COLUMNS.match(line)
            if global_columns_match is None:
                return super().parse_comment_line(line, root)
            global_columns = global_columns_match.group(1)
            self.node_attributes = [COLUMN_MAP.get(v, v.lower()) for v in global_columns.split(" ")]
            root.comment += line + '\n'
            return
        return super().parse_comment_line(line, root)

    def parse_node_line(self, line, root, nodes, parents, mwts):
        fields = line.split('\t')
        if len(fields) != len(self.node_attributes):
            if self.strict:
                raise RuntimeError('Wrong number of columns in %r' % line)
            fields.extend(['_'] * (len(self.node_attributes) - len(fields)))

        # multi-word tokens will be processed later
        if '-' in fields[0]:
            mwts.append(fields)
            return
        if '.' in fields[0]:
            raise NotImplementedError("Empty nodes in CoNLL-UPlus not implement yet in read.Conllup")

        # This implementation is slower than in read.Conllu,
        # but it allows for arbitrary columns
        node = root.create_child()
        nonstandard_attrs = []
        for (n_attribute, attribute_name) in enumerate(self.node_attributes):
            value = fields[n_attribute]
            if attribute_name == 'head':
                if value == '???':
                    value = 0
                try:
                    parents.append(int(value))
                except ValueError as exception:
                    if not self.strict and value == '_':
                        if self.empty_parent == 'warn':
                            logging.warning("Empty parent/head index in '%s'", line)
                        parents.append(0)
                    else:
                        raise exception
            elif attribute_name == 'ord':
                if int(value) != node._ord:
                    raise ValueError(f"Node {node} ord mismatch: {value}, but expecting {node._ord} at:\n{line}")
            elif attribute_name == 'deps':
                setattr(node, 'raw_deps', value)
            elif value == '_' and attribute_name != 'form':
                pass
            elif attribute_name == '_':
                pass
            elif attribute_name in NORMAL_ATTRS:
                setattr(node, attribute_name, value)
            else:
                nonstandard_attrs.append([attribute_name, value])

        # This needs to be done after node.misc is created (if "misc" in node.attributes)
        for attribute_name, value in nonstandard_attrs:
            node.misc[attribute_name.capitalize()] = value

        nodes.append(node)
