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

        # If tree.comment contains placeholders $NEWDOC,...$TEXT, replace them with the actual
        # value of the attribute and make note on which line (i_*) they were present.
        comment_lines = tree.comment.splitlines()
        i_newdoc, i_newpar, i_sent_id, i_text, i_global_entity = -1, -1, -1, -1, -1
        for i, c_line in enumerate(comment_lines):
            if c_line == '$SENT_ID':
                i_sent_id = i
                comment_lines[i] = ' sent_id = ' + tree.sent_id if self.print_sent_id else None
            elif c_line == '$TEXT':
                i_text = i
                if self.print_text:
                    if tree.text is None:
                        comment_lines[i] = ' text = ' + tree.compute_text()
                    else:
                        comment_lines[i] = ' text = ' + tree.text.replace('\n', '').replace('\r', '').rstrip()
            elif c_line == '$NEWDOC':
                i_newdoc = i
                if self.print_sent_id and tree.newdoc:
                    comment_lines[i] = ' newdoc' + (' id = ' + tree.newdoc if tree.newdoc is not True else '')
                else:
                    comment_lines[i] = None
            elif c_line == '$NEWPAR':
                i_newpar = i
                if self.print_sent_id and tree.newpar:
                    comment_lines[i] = ' newpar' + (' id = ' + tree.newpar if tree.newpar is not True else '')
                else:
                    comment_lines[i] = None
            elif c_line == '$GLOBAL.ENTITY':
                i_global_entity = i
                ge = tree.document.meta.get('global.Entity')
                if ge:
                    comment_lines[i] = ' global.Entity = ' + ge
                else:
                    comment_lines[i] = None

        # Now print the special comments: global.columns, newdoc, newpar, sent_id and text.
        # If these comments were already present in tree.comment (as marked with the placeholders),
        # keep them at their original position and print also all comment lines preceding them.
        # It they were missing, try to print them at the correct position.
        printed_i = -1
        if comment_lines and comment_lines[0].startswith(' global.columns'):
            printed_i += 1
            print('#' + comment_lines[printed_i])
        if self.print_sent_id:
            if tree.newdoc:
                if i_newdoc == -1:
                    print('# newdoc' + (' id = ' + tree.newdoc if tree.newdoc is not True else ''))
                else:
                    while printed_i < i_newdoc:
                        printed_i += 1
                        if comment_lines[printed_i]:
                            print('#' + comment_lines[printed_i])
                ge = tree.document.meta.get('global.Entity')
                if ge:
                    if i_global_entity == -1:
                        print('# global.Entity = ' + ge)
                    else:
                        while printed_i < i_global_entity:
                            printed_i += 1
                            if comment_lines[printed_i]:
                                print('#' + comment_lines[printed_i])
            if tree.newpar:
                if i_newpar == -1:
                    print('# newpar' + (' id = ' + tree.newpar if tree.newpar is not True else ''))
                else:
                    while printed_i < i_newpar:
                        printed_i += 1
                        if comment_lines[printed_i]:
                            print('#' + comment_lines[printed_i])
            if i_sent_id == -1:
                print('# sent_id = ' + tree.sent_id)
            else:
                while printed_i < i_sent_id:
                    printed_i += 1
                    if comment_lines[printed_i]:
                        print('#' + comment_lines[printed_i])
        if self.print_text and i_text == -1:
            print('# text = ' + (tree.compute_text() if tree.text is None else tree.text.replace('\n', '').replace('\r', '').rstrip()))

        for c_line in comment_lines[printed_i + 1:]:
            if c_line:
                print('#' + c_line)

        # Special-purpose json_* comments should always be at the end of the comment block.
        if tree.json:
            for key, value in sorted(tree.json.items()):
                print(f"# json_{key} = {json.dumps(value, ensure_ascii=False, sort_keys=True)}")

        last_mwt_id = 0
        for node in nodes:
            mwt = node._mwt
            if mwt and node._ord > last_mwt_id:
                print('\t'.join((mwt.ord_range,
                                 '_' if mwt.form is None else mwt.form,
                                 '_\t_\t_\t_\t_\t_\t_',
                                 '_' if mwt._misc is None else str(mwt.misc))))
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
