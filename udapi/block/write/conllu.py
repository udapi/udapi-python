"""Conllu class is a a writer of files in the CoNLL-U format."""
from udapi.core.basewriter import BaseWriter


class Conllu(BaseWriter):
    """A writer of files in the CoNLL-U format."""

    def __init__(self, print_sent_id=True, print_text=True, print_empty_trees=True, **kwargs):
        super().__init__(**kwargs)
        self.print_sent_id = print_sent_id
        self.print_text = print_text
        self.print_empty_trees = print_empty_trees

        # A list of Conllu columns.
        self.node_attributes = ["ord", "form", "lemma", "upos", "xpos",
                                "feats", "parent", "deprel", "raw_deps", "misc"]

    def process_tree(self, tree):
        nodes = tree.descendants

        # Empty sentences are not allowed in CoNLL-U, so with print_empty_trees==0
        # we need to skip the whole tree (including possible comments).
        if not nodes and not self.print_empty_trees:
            return

        if self.print_sent_id:
            print('# sent_id = ' + tree.address())

        if self.print_text:
            print("# text = " + tree.get_sentence())

        comment = tree.comment
        if comment:
            comment = comment.rstrip()
            print('#' + comment.replace('\n', '\n#'))

        last_mwt_id = 0
        for node in nodes:
            mwt = node.multiword_token
            if mwt and node.ord > last_mwt_id:
                last_mwt_id = mwt.words[-1].ord
                print('\t'.join([mwt.ord_range(),
                                 mwt.form if mwt.form is not None else '_',
                                 '_\t_\t_\t_\t_\t_\t_', str(mwt.misc)]))
            values = [str(getattr(node, attr_name)) for attr_name in self.node_attributes]
            try:
                values[6] = str(node.parent.ord)
            except AttributeError:
                values[6] = '0'
            for index in range(0, len(values)):
                if values[index] is None:
                    values[index] = '_'
            print('\t'.join(values))

        # Empty sentences are not allowed in CoNLL-U,
        # but with print_empty_trees==1 (which is the default),
        # we will print an artificial node, so we can print the comments.
        if not nodes:
            print("1\t_\t_\t_\t_\t_\t0\t_\t_\tEmpty=Yes")

        # Empty line separates trees in CoNLL-U (and is required after the last tree as well)
        print("")
