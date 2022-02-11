""""Conllu is a reader block for the CoNLL-U files."""
import json
import logging
import re

from udapi.core.basereader import BaseReader
from udapi.core.root import Root
from udapi.core.node import Node

# Compile a set of regular expressions that will be searched over the lines.
# The equal sign after sent_id was added to the specification in UD v2.0.
# This reader accepts also older-style sent_id (until UD v2.0 treebanks are released).
RE_SENT_ID = re.compile(r'^# sent_id\s*=?\s*(\S+)')
RE_TEXT = re.compile(r'^# text\s*=\s*(.*)')
RE_NEWPARDOC = re.compile(r'^# (newpar|newdoc)(?:\s+id\s*=\s*(.+))?$')
RE_JSON = re.compile(r'^# (doc_)?json_([^ =]+)\s*=\s*(.+)')
RE_GLOBAL_ENTITY = re.compile(r'^# global.Entity\s*=\s*(\S+)')


class Conllu(BaseReader):
    """A reader of the CoNLL-U files."""

    def __init__(self, strict=False, empty_parent='warn', fix_cycles=False, **kwargs):
        """Create the Conllu reader object.

        Args:
        strict: raise an exception if errors found (default=False, i.e. a robust mode)
        empty_parent: What to do if HEAD is _? Default=warn: issue a warning and attach to the root
            or if strict=1 issue an exception. With `empty_parent=ignore` no warning is issued.
        fix_cycles: fix cycles by attaching a node in the cycle to the root
        """
        super().__init__(**kwargs)
        self.strict = strict
        self.empty_parent = empty_parent
        self.fix_cycles = fix_cycles

    def parse_comment_line(self, line, root):
        """Parse one line of CoNLL-U and fill sent_id, text, newpar, newdoc in root."""
        sent_id_match = RE_SENT_ID.match(line)
        if sent_id_match is not None:
            root.sent_id = sent_id_match.group(1)
            root.comment += '$SENT_ID\n'
            return

        text_match = RE_TEXT.match(line)
        if text_match is not None:
            root.text = text_match.group(1)
            root.comment += '$TEXT\n'
            return

        pardoc_match = RE_NEWPARDOC.match(line)
        if pardoc_match is not None:
            value = True if pardoc_match.group(2) is None else pardoc_match.group(2)
            if pardoc_match.group(1) == 'newpar':
                root.newpar = value
                root.comment += '$NEWPAR\n'
            else:
                root.newdoc = value
                root.comment += '$NEWDOC\n'
            return

        json_match = RE_JSON.match(line)
        if json_match is not None:
            container = root.json
            if json_match.group(1) == 'doc_':
                if '__doc__' not in root.json:
                    root.json['__doc__'] = {}
                container = root.json['__doc__']
            container[json_match.group(2)] = json.loads(json_match.group(3))
            return

        entity_match = RE_GLOBAL_ENTITY.match(line)
        if entity_match is not None:
            global_entity = entity_match.group(1)
            if self._global_entity and self._global_entity != global_entity:
                logging.warning("Mismatch in global.Entity: %s != %s", (self._global_entity, global_entity))
            self._global_entity = global_entity
            root.comment += '$GLOBAL.ENTITY\n'
            return

        root.comment += line[1:] + "\n"

    def read_trees(self):
        return [self.read_tree_from_lines(s.split('\n')) for s in
                self.filehandle.read().split('\n\n') if s]

    def read_tree(self):
        if self.filehandle is None:
            return None
        lines = []
        for line in self.filehandle:
            line = line.rstrip()
            if line == '':
                break
            lines.append(line)
        return self.read_tree_from_lines(lines)

    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    # Maybe the code could be refactored, but it is speed-critical,
    # so benchmarking is needed because calling extra methods may result in slowdown.
    def read_tree_from_lines(self, lines):
        root = Root()
        nodes = [root]
        parents = [0]
        mwts = []
        for line in lines:
            if line[0] == '#':
                self.parse_comment_line(line, root)
            else:
                fields = line.split('\t')
                if len(fields) != 10:
                    if self.strict:
                        raise RuntimeError('Wrong number of columns in %r' % line)
                    fields.extend(['_'] * (10 - len(fields)))
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

                if fields[3] == '_':
                    fields[3] = None
                if fields[4] == '_':
                    fields[4] = None
                if fields[7] == '_':
                    fields[7] = None

                # ord,form,lemma,upos,xpos,feats,head,deprel,deps,misc
                node = Node(root=root, form=fields[1], lemma=fields[2], upos=fields[3],
                            xpos=fields[4], feats=fields[5], deprel=fields[7], misc=fields[9])
                root._descendants.append(node)
                node._ord = int(fields[0])
                if fields[8] != '_':
                    node.raw_deps = fields[8]
                try:
                    parents.append(int(fields[6]))
                except ValueError as exception:
                    if not self.strict and fields[6] == '_':
                        if self.empty_parent == 'warn':
                            logging.warning("Empty parent/head index in '%s'", line)
                        parents.append(0)
                    else:
                        raise exception

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
