"""Vislcg is a reader block the VISL-cg format."""
from udapi.core.basereader import BaseReader
from udapi.core.root import Root


class Vislcg(BaseReader):
    """A reader of the VISL-cg format, suitable for VISL Constraint Grammer Parser."""

    # TODO check validity and raise helpful exceptions if not valid
    # pylint: disable=too-many-branches
    def read_tree(self):
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
                root.comment += line[1:] + "\n"
                continue

            if line[0].isspace():
                node, parent_ord = self._node(line.lstrip(), root)
                words.append(node)
                parents.append(parent_ord)
                continue

            if words:
                words[0].form = form
                if len(words) > 1:
                    split_forms = form.split()
                    if len(words) == len(split_forms):
                        for word, split_form in zip(words, split_forms):
                            word.form = split_form
                    else:
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
        # line contains "lemma" xpos feat1 feat2 .. featN @deprel #ord->parent.ord
        # Lemma can contain spaces, but quotes within lemma are not escaped,
        # so we cannot use fields = shlex.split(line)
        # Let's hope that xpos, feats and deprel do not contain any quotes.
        end_quote_pos = line.rfind('"')
        lemma = line[1:end_quote_pos]
        fields = line[end_quote_pos + 1:].split()
        xpos = fields[0]
        feats_list = fields[3:-2]
        feats = '|'.join(feats_list) if feats_list else '_'
        deprel = fields[-2][1:]
        parent_ord = int(fields[-1].split('->')[1])
        node = root.create_child(lemma=lemma, xpos=xpos, feats=feats, deprel=deprel)
        return node, parent_ord
