"""An ASCII pretty printer of dependency trees."""
import re
import sys

import colorama
from termcolor import colored
from udapi.core.basewriter import BaseWriter

COLOR_OF = {
    'form': 'yellow',
    'lemma': 'cyan',
    'upos': 'red',
    'deprel': 'blue',
    'ord': 'yellow',
}

def _length(string):
    '''Strips ANSI color codes before measuring the string's length.'''
    return len(re.sub(r'\x1b\[([0-9,A-Z]{1,2}(;[0-9]{1,2})?(;[0-9]{3})?)?[m|K]?', '', string))

# Too many instance variables, arguments, branches...
# I don't see how to fix this while not making the code less readable or more difficult to use.
# pylint: disable=R0902,R0912,R0913,R0914
class TextModeTrees(BaseWriter):
    """An ASCII pretty printer of dependency trees.

    SYNOPSIS
    # from command line (visualize CoNLL-U files)
    udapy write.TextModeTrees color=1 < file.conllu | less -R

    # is scenario (examples of other parameters)
    write.TextModeTrees indent=1 print_sent_id=1 print_sentence=1
    write.TextModeTrees zones=en,cs attributes=form,lemma,upos minimize_cross=0

    DESCRIPTION
    This block prints dependency trees in plain-text format.
    For example the following CoNLL-U file (with tabs instead of spaces)

    1  I     I     PRON  PRP Number=Sing|Person=1 2 nsubj      _ _
    2  saw   see   VERB  VBD Tense=Past           0  root      _ _
    3  a     a     DET   DT  Definite=Ind         4  det       _ _
    4  dog   dog   NOUN  NN  Number=Sing          2  dobj      _ _
    5  today today NOUN  NN  Number=Sing          2  nmod:tmod _ SpaceAfter=No
    6  ,     ,     PUNCT ,   _                    2  punct     _ _
    7  which which DET   WDT PronType=Rel         10 nsubj     _ _
    8  was   be    VERB  VBD Person=3|Tense=Past  10 cop       _ _
    9  a     a     DET   DT  Definite=Ind         10 det       _ _
    10 boxer boxer NOUN  NN  Number=Sing          4  acl:relcl _ SpaceAfter=No
    11 .     .     PUNCT .   _                    2  punct     _ _

    will be printed (with the default parameters) as
    ─┐
     │ ┌──I PRON nsubj
     └─┤saw VERB root
       │                           ┌──a DET det
       ├───────────────────────────┤dog NOUN dobj
       ├──yesterday NOUN nmod:tmod │
       ├──, PUNCT punct            │
       │                           │ ┌──which DET nsubj
       │                           │ ├──was VERB cop
       │                           │ ├──a DET det
       │                           └─┘boxer NOUN acl:relcl
       └──. PUNCT punct

    This block's method process_tree can be called on any node (not only root),
    which is useful for printing subtrees using node.print_subtree(),
    which is internally implemented using this block.
    """

    def __init__(self, print_sent_id=False, print_sentence=False, add_empty_line=True, indent=1,
                 minimize_cross=True, color='auto', attributes='form,upos,deprel',
                 print_undef_as='', **kwargs):
        """Create new TextModeTrees block object.

        Args:
        print_sent_id: Print ID of the tree (its root, aka "sent_id") above each tree?
        print_sentence: Print plain-text detokenized sentence on a line above each tree?
        add_empty_line: Print an empty line after each tree?
        indent: Number of characters to indent node depth in the tree for better readability.
        minimize_cross: Minimize crossings of edges in non-projective trees?
                        Trees without crossings are subjectively more readable, but usually
                        in practice also "deeper", that is with higher maximal line length.
        color: Print the node attribute with ANSI terminal colors?
               Default = 'auto' which means that color output only if the output filehandle
               is interactive (console). Each attribute is assigned a color (the mapping is
               tested on black background terminals and can be changed only in source code).
               If you plan to pipe the output (e.g. to "less -R") and you want the colors,
               you need to set explicitly color=1, see the example in Synopsis.
        attributes: A comma-separated list of node attributes which should be printed. Possible
                    values are ord, form, lemma, upos, xpos, feats, deprel, deps, misc.
        print_undef_as: What should be printed instead of undefined attribute values (if any)?
        """
        super().__init__(**kwargs)
        self.print_sent_id = print_sent_id
        self.print_sentence = print_sentence
        self.add_empty_line = add_empty_line
        self.indent = indent
        self.minimize_cross = minimize_cross
        self.color = color
        self.attributes = attributes
        self.print_undef_as = print_undef_as

        # _draw[is_bottommost][is_topmost]
        line = '─' * indent
        self._horiz = line + '─'
        self._draw = [[line + '┤', line + '┐'], [line + '┘', self._horiz]]

        # _space[is_bottommost][is_topmost]
        # _vert[is_crossing]
        space = ' ' * indent
        self._space = [[space + '├', space + '┌'], [space + '└']]
        self._vert = [space + '│', line + '╪']

        self.attrs = attributes.split(',')
        self._index_of = []
        self._gaps = []

    # We want to be able to call process_tree not only on root node,
    # so this block can be called from node.print_subtree(**kwargs)
    # on any node and print its subtree. Thus, we cannot assume that
    # allnodes[idx].ord == idx. Instead of node.ord, we'll use index_of[node.ord],
    # which is its index within the printed subtree.
    # gaps[node.ord] = number of nodes within node's span, which are not its descendants.
    def _compute_gaps(self, node):
        lmost, rmost, descs = self._index_of[node.ord], self._index_of[node.ord], 0
        for child in node.children:
            _lm, _rm, _de = self._compute_gaps(child)
            lmost = min(_lm, lmost)
            rmost = max(_rm, rmost)
            descs += _de
        self._gaps[node.ord] = rmost - lmost - descs
        return lmost, rmost, descs + 1

    def process_tree(self, root):
        """Print the tree to (possibly redirected) sys.stdout."""
        allnodes = [root] + root.descendants()
        self._index_of = {allnodes[i].ord: i for i in range(len(allnodes))}
        lines = [''] * len(allnodes)

        # Precompute the number of non-projective gaps for each subtree
        if self.minimize_cross:
            self._gaps = [0,] * (1 + len(root.root.descendants))
            self._compute_gaps(root)

        # Precompute lines for printing
        stack = [root,]
        while stack:
            node = stack.pop()
            children = node.children(add_self=1)
            min_idx, max_idx = self._index_of[children[0].ord], self._index_of[children[-1].ord]
            max_length = max([_length(lines[i]) for i in range(min_idx, max_idx+1)])
            for idx in range(min_idx, max_idx+1):
                idx_node = allnodes[idx]
                filler = '─' if lines[idx] and lines[idx][-1] in '─┌└├╪' else ' '
                lines[idx] += filler * (max_length - _length(lines[idx]))

                topmost = idx == min_idx
                botmost = idx == max_idx
                if idx_node is node:
                    lines[idx] += self._draw[botmost][topmost] + self.node_to_string(node)
                else:
                    if idx_node.parent is not node:
                        lines[idx] += self._vert[bool(lines[idx] and lines[idx][-1] == '─')]
                    else:
                        lines[idx] += self._space[botmost][topmost]
                        if idx_node.is_leaf():
                            lines[idx] += self._horiz + self.node_to_string(idx_node)
                        else:
                            stack.append(idx_node)

            # sorting the stack to minimize crossings of edges
            if self.minimize_cross:
                stack = sorted(stack, key=lambda x: -self._gaps[x.ord])

        # Print headers (if required) and the tree itself
        if self.print_sent_id:
            print('# sent_id = ' + root.address())
        if self.print_sentence:
            print("# text = " + root.compute_sentence())
        for line in lines:
            print(line)

        if self.add_empty_line:
            print('')

    def before_process_document(self, document):
        """Initialize ANSI colors if color is True or 'auto'.

        If color=='auto', detect if sys.stdout is interactive
        (terminal, not redirected to a file).
        """
        super().before_process_document(document)
        if self.color == 'auto':
            self.color = sys.stdout.isatty()
            if self.color:
                colorama.init()

    def node_to_string(self, node):
        """Render a node with its attributes."""
        if node.is_root():
            return ''
        values = node.get_attrs(self.attrs, undefs=self.print_undef_as)
        if self.color:
            for i, attr in enumerate(self.attrs):
                color = COLOR_OF.get(attr, 0)
                if color:
                    values[i] = colored(values[i], color)
        return ' '.join(values)
