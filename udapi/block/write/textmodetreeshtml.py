"""An ASCII pretty printer of colored dependency trees in HTML."""
from html import escape  # pylint: disable=no-name-in-module

from udapi.block.write.textmodetrees import TextModeTrees

# White background is better for printing, so let's choose dark text colors.
# Highlighting marked nodes should not change positioning and break the vertical lines alignment,
# so we cannot use standard border, but box-shadow.
STYLE = '''
  .form {color: maroon;}
  .lemma {color: purple;}
  .upos {color: red;}
  .deprel {color: blue;}
  .ord {color: green;}
  mark {box-shadow: 0px 0px 0px 1px red; font-weight: bold;}
'''


class TextModeTreesHtml(TextModeTrees):
    """An ASCII pretty printer of colored dependency trees in HTML.

    SYNOPSIS
    # from command line (visualize CoNLL-U files)
    udapy write.TextModeTreesHtml < file.conllu > file.html

    This block is a subclass of `TextModeTrees`, see its documentation for more info.
    """

    def __init__(self, color=True, title='Udapi visualization', zones_in_rows=True, whole_bundle=True, **kwargs):
        """Create new TextModeTreesHtml block object.

        Args: see `TextModeTrees`.
        Color is by default set to `True` (even if the output is redirected to a file of pipe).
        You can force `color=0` e.g. if you want the node highlighting
        (see the `mark` parameter) to be more eye-catching.

        title: What title metadata to use for the html?
        zones_in_rows: print trees from the same bundle side by side (i.e. in the same row).
        whole_bundle: always print the whole bundle (all its trees) if any of the trees is marked
        (relevant only with marked_only=True and zones_in_rows=True)
        """
        super().__init__(color=color, **kwargs)
        self.title = title
        self.zones_in_rows = zones_in_rows
        self.whole_bundle = whole_bundle

    def before_process_document(self, document):
        # TextModeTrees.before_process_document changes the color property,
        # we need to skip this, but call BaseWriter's method which redirects stdout.
        # pylint: disable=bad-super-call
        super(TextModeTrees, self).before_process_document(document)
        print('<!DOCTYPE html>\n<html>\n<head>\n<meta charset="utf-8">')
        print('<title>' + self.title + '</title>')
        print('<style>' + STYLE)
        print('</style>\n</head>\n<body>\n<pre>')
        if self.print_doc_meta:
            for key, value in sorted(document.meta.items()):
                print('%s = %s' % (key, value))

    def after_process_document(self, document):
        print("</pre>\n</body>\n</html>")
        super().after_process_document(document)

    def add_node(self, idx, node):
        if not node.is_root():
            marked = self.is_marked(node)
            self.lines[idx] += '<mark>' if marked else ''
            super().add_node(idx, node)
            self.lines[idx] += '</mark>' if marked else ''

    def colorize_comment(self, comment):
        """Return a string with color markup for a given comment."""
        if self.mark_re is None:
            return comment
        return self.comment_mark_re.sub(r'<mark>\g<0></mark>', comment)

    @staticmethod
    def colorize_attr(attr, value, marked):
        """Return a string with color markup for a given attr and its value."""
        return "<span class='%s'>%s</span>" % (attr, escape(value))

    def print_headers(self, root):
        if self.print_sent_id:
            print('# sent_id = ' + escape(root.address()))
        if self.print_text:
            text = "# text = " + (root.get_sentence() if root.is_root() else root.compute_text())
            print(escape(text))
        if self.print_comments and root.comment:
            print('#' + self.colorize_comment(escape(root.comment)).rstrip().replace('\n', '\n#'))

    def process_bundle(self, bundle):
        if self.zones_in_rows:
            # Don't print <table><tr></tr></table> if no tree will be printed in this bundle.
            marked_trees = []
            for tree in bundle:
                if self._should_process_tree(tree):
                    if self.print_empty:
                        allnodes = [tree] + tree.descendants_and_empty
                    else:
                        allnodes = tree.descendants(add_self=1)
                if self.should_print_tree(tree, allnodes):
                    marked_trees.append(tree)
            if marked_trees:
                if self.whole_bundle:
                    marked_trees = bundle
                print("<table><tr>")
                for tree in marked_trees:
                    print("<td>")
                    self.process_tree(tree, force_print=True)
                    print("</td>")
                print("</tr></table>")
        else:
            super().process_bundle(bundle)
