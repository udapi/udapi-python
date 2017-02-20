"""Vislcg is a reader block the VISL-cg format."""
from udapi.core.basereader import BaseReader
from udapi.core.root import Root

class Vislcg(BaseReader):
    """A reader of the VISL-cg format, suitable for VISL Constraint Grammer Parser."""

    # TODO check validity and raise helpful exceptions if not valid
    # pylint: disable=too-many-branches
    def read_tree(self, document=None):
        if self.filehandle is None:
            return None

        root = Root()
        parents = [0]
        words = []
        form = None
        for line in self.filehandle:
            line = line.rstrip()
            if line == '':
                break
            if line[0] == '#':
                # Are comments allowed in VISL-cg?
                continue

            if line[0].isspace():
                line.lstrip(line)
                node, parent_ord = self._node(line, root)
                words.append(node)
                parents.append(parent_ord)
            else:
                if words:
                    words[0].form = form
                    if len(words) > 1:
                        for word in words[1:]:
                            word.form = '_'
                        root.create_multiword_token(words, form=form)
                    words = []
                form = line[2:-2]

        if words:
            words[0].form = form
            for word in words[1:]:
                word.form = '_'

        nodes = root.descendants(add_self=True)
        if len(nodes) == 1:
            return None
        for node_ord, node in enumerate(nodes[1:], 1):
            try:
                node.parent = nodes[parents[node_ord]]
            except IndexError:
                raise ValueError("Node %s HEAD is out of range (%d)" % (node, parents[node_ord]))

        return root

    @staticmethod
    def _node(line, root):
        fields = line.split()
        lemma = fields[0][1:-1]
        xpos = fields[1]
        feats_list = fields[2:-2]
        feats = '|'.join(feats_list) if feats_list else '_'
        deprel = fields[-2][1:]
        parent_ord = int(fields[-1].split('->')[1])
        node = root.create_child(lemma=lemma, xpos=xpos, feats=feats, deprel=deprel)
        return node, parent_ord
