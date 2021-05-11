"""Tikz class is a writer for LaTeX with tikz-dependency."""
import logging

from udapi.core.basewriter import BaseWriter


class Tikz(BaseWriter):
    r"""A writer of files in the LaTeX with tikz-dependency format.

    Usage::

      udapy write.Tikz < my.conllu > my.tex
      # or for 2D tree-like rendering
      udapy write.Tikz as_tree=1 < my.conllu > my.tex
      pdflatex my.tex
      xdg-open my.pdf

    Long sentences may result in too large pictures.
    You can tune the width (in addition to changing fontsize or using minipage and rescaling) with
    ``\begin{deptext}[column sep=0.2cm]``
    or individually for each word:
    ``My \&[.5cm] dog \& etc.``
    By default, the height of the horizontal segment of a dependency edge is proportional
    to the distance between the linked words. You can tune the height with:
    ``\depedge[edge unit distance=1.5ex]{9}{1}{deprel}``

    See `tikz-dependency documentation
    <http://mirrors.ctan.org/graphics/pgf/contrib/tikz-dependency/tikz-dependency-doc.pdf>`_
    for details.

    With ``as_tree=1``, there are two options how to visualize deprels:
    either as labels positioned on the edges by uncommenting the relevant style definition,
    or by adding ``deprel`` to the list of attributes, so deprels are above/below the words.
    The latter is the default because the edge labels need manual tweaks to prevent overlapping.

    Alternatives:
    * use `write.TextModeTrees` and include it in verbatim environment in LaTeX.
    * use `write.Html`, press "Save as SVG" button, convert to pdf and include in LaTeX.
    """

    def __init__(self, print_sent_id=True, print_text=True, print_preambule=True,
                 attributes=None, as_tree=False, comment_attribute=None, **kwargs):
        """Create the Tikz block object.

        Args:
        print_sent_id: print sent_id (`tree.address()`) as a LaTeX comment (default=True)
        print_text: print sentence text  (`tree.get_sentence()`) as a LaTeX comment (default=True)
        print_preambule: surround each document with LaTeX preambule (`documentclass` etc)
            and `end{document}` (default=True)
        attributes: comma-separated list of node attributes to print (each on a separate line).
        as_tree: boolean - should print it as a 2D tree?
        comment_attribute: which attribute to print as a string under each graph (e.g. text_en)
        """
        super().__init__(**kwargs)
        self.print_sent_id = print_sent_id
        self.print_text = print_text
        self.print_preambule = print_preambule
        if attributes is not None:
           self.node_attributes = attributes.split(',')
        elif as_tree:
            self.node_attributes = 'form,upos,deprel'.split(',')
        else:
            self.node_attributes = 'form,upos'.split(',')
        self.as_tree = as_tree
        self.comment_attribute = comment_attribute

    def before_process_document(self, doc):
        super().before_process_document(doc)
        if self.print_preambule:
            print(r'\documentclass[multi=dependency]{standalone}')
            print(r'\usepackage[T1]{fontenc}')
            print(r'\usepackage[utf8]{inputenc}')
            print(r'\usepackage{tikz-dependency}')
            if self.as_tree:
                print(r'\tikzset{depedge/.style = {blue,thick}, %,<-')
                print(r'  deplabel/.style = {opacity=0, %black, fill opacity=0.9, text opacity=1,')
                print(r'   % yshift=4pt, pos=0.1, inner sep=0, fill=white, font={\scriptsize}')
                print(r'  },')
                print(r'  depnode/.style = {draw,circle,fill,blue,inner sep=1.5pt},')
                print(r'  depguide/.style = {dashed,gray},')
                print(r'}')
                print(r'\newlength{\deplevel}\setlength{\deplevel}{8mm}')
                print(r'\newlength{\depskip}\setlength{\depskip}{4mm}')
            print(r'\newcommand{\deptrans}[1]{\node (t) at (\matrixref.south)[yshift=-1mm]'
                  " {``#1''};}")
            print(r'\begin{document}')

    def after_process_document(self, doc):
        if self.print_preambule:
            print(r'\end{document}')
        logging.info('Use pdflatex to compile the output')
        super().after_process_document(doc)

    def _tex_escape(self, string):
        return string.replace('_', r'\_').replace('$', '\$').replace('[', '$[$').replace(']', '$]$')

    def process_tree(self, tree):
        print(r'\begin{dependency}')
        print(r'\begin{deptext}')
        nodes = tree.descendants

        if self.print_sent_id:
            print('% sent_id = ' + tree.address())

        if self.print_text:
            print("% text = " + tree.get_sentence())

        comment = tree.comment
        if comment:
            comment = comment.rstrip()
            print('%' + comment.replace('\n', '\n%'))

        lines = ['' for _ in self.node_attributes]
        for node in nodes:
            values = [self._tex_escape(v) for v in node.get_attrs(self.node_attributes)]
            max_len = max(len(value) for value in values)
            for index, value in enumerate(values):
                if node.ord > 1:
                    lines[index] += r' \& '
                lines[index] += value.ljust(max_len)
        for line in lines:
            print(line + r' \\')
        print(r'\end{deptext}')
        if self.as_tree:
            depths = [n._get_attr('depth') for n in nodes]
            max_depth = max(depths)
            for node in nodes:
                print(r'\node (w%d) [yshift=\depskip+%s\deplevel,depnode] at (\wordref{1}{%d}) {};'
                      % (node.ord, max_depth - depths[node.ord - 1], node.ord))
            for node in nodes:
                print(r'\draw[depguide] (w%d)--(\wordref{1}{%d});'  % (node.ord, node.ord), end='')
                if node.parent.is_root():
                    print('')
                else:
                    print(r' \draw[depedge] (w%d)--node[deplabel] {%s} (w%d);'
                          % (node.ord, node.deprel, node.parent.ord))
        else:
            for node in nodes:
                if node.parent.is_root():
                    print(r'\deproot{%d}{root}' % node.ord)
                else:
                    print(r'\depedge{%d}{%d}{%s}' % (node.parent.ord, node.ord, node.deprel))
        if self.comment_attribute and tree.comment:
            start_pos = tree.comment.find(self.comment_attribute + ' = ')
            if start_pos != -1:
                start_pos += len(self.comment_attribute) + 3
                end_pos = tree.comment.find('\n', start_pos)
                print(r'\deptrans{' + tree.comment[start_pos:end_pos])

        print(r'\end{dependency}')
        print('')  # empty line marks a new paragraph in LaTeX, but multi=dependency causes newpage
