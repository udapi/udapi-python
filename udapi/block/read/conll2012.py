""""Conll2012 is a reader block for the coreference in CoNLL-2012 format.

This implementation was tested on the LitBank files only, so far.
LitBank does not use most of the columns, so the implementation
should be improved to handle other types of CoNLL-2012 files.
"""
import json
import logging
import re

import udapi.block.read.conllu
from udapi.core.root import Root
from udapi.core.node import Node

#RE_BEGIN = re.compile(r'^#begin document \(([^)]+)\); part (\d+)')
RE_BEGIN = re.compile(r'^#begin document \(([^)]+)\)')

class Conll2012(udapi.block.read.conllu.Conllu):
    """A reader of the Conll2012 files."""

    def __init__(self, attributes='docname,_,ord,form,_,_,_,_,_,_,_,_,coref', **kwargs):
        """Create the Conll2012 reader object.

        Args:
        attributes: comma-separated list of column names in the input files
            (default='docname,_,ord,form,_,_,_,_,_,_,_,_,coref')
            For ignoring a column, use "_" as its name.
            Column "ord" marks the column with 0-based (unlike in CoNLL-U, which uses 1-based)
            word-order number/index (usualy called ID).
        """
        super().__init__(**kwargs)
        self.node_attributes = attributes.split(',')
        self._docname = 'd'

    def parse_comment_line(self, line, root):
        if line.startswith("#end document"):
            return
        match = RE_BEGIN.match(line)
        if match:
            docname = match.group(1)
            root.newdoc = docname
            self._global_entity = 'eid-etype-head-other'
            root.comment += '$GLOBAL.ENTITY\n'
            self._docname = docname
        else:
            logging.warning(f"Unexpected comment line: {line}")

    def parse_node_line(self, line, root, nodes):
        fields = line.split('\t')
        if len(fields) != len(self.node_attributes):
            if self.strict:
                raise RuntimeError('Wrong number of columns in %r' % line)
            fields.extend(['_'] * (len(self.node_attributes) - len(fields)))

        # This implementation is slower than in read.Conllu,
        # but it allows for arbitrary columns
        node = root.create_child()
        for (n_attribute, attribute_name) in enumerate(self.node_attributes):
            value = fields[n_attribute]
            if attribute_name == 'docname':
                if value != self._docname:
                    logging.warning(f"Document name mismatch {value} != {self._docname}")

            # convert the zero-based index to one-based
            elif attribute_name == 'ord':
                setattr(node, 'ord', int(value) + 1)

            elif attribute_name == 'coref':
                if value and value != '_':
                    entities = value.split("|")
                    modified_entities = []
                    escaped_docname = self._docname.replace("-", "")
                    for entity in entities:
                        entity_num = entity.replace("(", "").replace(")","")
                        modified_entity = f"{escaped_docname}_e{entity_num}--1"
                        if entity.startswith("(") and entity.endswith(")"):
                            modified_entity = "(" + modified_entity + ")"
                        elif entity.startswith("("):
                            modified_entity = "(" + modified_entity
                        elif entity.endswith(")"):
                            modified_entity = f"{escaped_docname}_e{entity_num}" + ")"

                        # to avoid parentheses clashes, put the entities with ")" first
                        if modified_entity.startswith("("):
                            modified_entities.append(modified_entity)
                        else:
                            modified_entities.insert(0, modified_entity)
                    node.misc['Entity'] = ''.join(modified_entities)

            elif attribute_name == 'form' or (attribute_name != '_' and value != '_'):
                setattr(node, attribute_name, value)
        nodes.append(node)

    def read_tree_from_lines(self, lines):
        root = Root()
        nodes = [root]
        for line in lines:
            if line == '':
                pass
            elif line[0] == '#':
                self.parse_comment_line(line, root)
            else:
                self.parse_node_line(line, root, nodes)

        # If no nodes were read from the filehandle (so only root remained in nodes),
        # we return None as a sign of failure (end of file or more than one empty line).
        if len(nodes) == 1:
            return None

        return root
