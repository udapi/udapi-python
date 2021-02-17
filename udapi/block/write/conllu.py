"""Conllu class is a a writer of files in the CoNLL-U format."""
import json
from udapi.core.basewriter import BaseWriter


class Conllu(BaseWriter):
    """A writer of files in the CoNLL-U format."""

    def __init__(self, print_sent_id=True, print_text=True, print_empty_trees=True, **kwargs):
        super().__init__(**kwargs)
        self.print_sent_id = print_sent_id
        self.print_text = print_text
        self.print_empty_trees = print_empty_trees

    def process_tree(self, tree):  # pylint: disable=too-many-branches
        empty_nodes = tree.empty_nodes
        if empty_nodes:
            nodes = sorted(tree._descendants + empty_nodes)
        else:
            nodes = tree._descendants

        # Empty sentences are not allowed in CoNLL-U, so with print_empty_trees==0
        # we need to skip the whole tree (including possible comments).
        if not nodes and not self.print_empty_trees:
            return

        if self.print_sent_id:
            if tree.newdoc:
                 print('# newdoc' + (' id = ' + tree.newdoc if tree.newdoc is not True else ''))
            if tree.newpar:
                print('# newpar' + (' id = ' + tree.newpar if tree.newpar is not True else ''))
            print('# sent_id = ' + tree.sent_id)

        if self.print_text:
            print('# text = ' + (tree.text or tree.compute_text()))

        if tree.json:
            for key, value in sorted(tree.json.items()):
                print(f"# json_{key} = {json.dumps(value, ensure_ascii=False, sort_keys=True)}")

        comment = tree.comment
        if comment:
            print('#' + comment.rstrip().replace('\n', '\n#'))

        last_mwt_id = 0
        for node in nodes:
            mwt = node._mwt
            if mwt and node._ord > last_mwt_id:
                print('\t'.join((mwt.ord_range,
                                 '_' if mwt.form is None else mwt.form,
                                 '_\t_\t_\t_\t_\t_\t_',
                                 '_' if node._misc is None else str(mwt.misc))))
                last_mwt_id = mwt.words[-1]._ord

            if node._parent is None:
                head = '_' # Empty nodes
            else:
                try:
                    head = str(node._parent._ord)
                except AttributeError:
                    head = '0'

            print('\t'.join('_' if v is None else v for v in
                (str(node._ord), node.form, node.lemma, node.upos, node.xpos,
                '_' if node._feats is None else str(node.feats), head, node.deprel,
                node.raw_deps, '_' if node._misc is None else str(node.misc))))

        # Empty sentences are not allowed in CoNLL-U,
        # but with print_empty_trees==1 (which is the default),
        # we will print an artificial node, so we can print the comments.
        if not nodes:
            print("1\t_\t_\t_\t_\t_\t0\t_\t_\tEmpty=Yes")

        # Empty line separates trees in CoNLL-U (and is required after the last tree as well)
        print("")

    def before_process_document(self, document):
        """Print doc_json_* headers."""
        super().before_process_document(document)
        if document.json:
            for key, value in sorted(document.json.items()):
                print("# doc_json_%s = %s"
                      % (key, json.dumps(value, ensure_ascii=False, sort_keys=True)))
