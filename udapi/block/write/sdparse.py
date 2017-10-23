"""Sdparse class is a writer for Stanford dependencies format."""
import collections

from udapi.core.basewriter import BaseWriter


class Sdparse(BaseWriter):
    """A writer of files in the Stanford dependencies format, suitable for Brat visualization.

    Usage:
    ``udapy write.Sdparse print_upos=0 < in.conllu``

    Example output::

      ~~~ sdparse
      Corriere Sport da pagina 23 a pagina 26
      name(Corriere, Sport)
      case(pagina-4, da)
      nmod(Corriere, pagina-4)
      nummod(pagina-4, 23)
      case(pagina-7, a)
      nmod(Corriere, pagina-7)
      nummod(pagina-7, 26)
      ~~~

    To visualize it, use embedded Brat, e.g. go to
    http://universaldependencies.org/visualization.html#editing.
    Click the edit button and paste the output of this writer excluding the `~~~` marks.

    Notes:
    The original `Stanford dependencies format
    <https://nlp.stanford.edu/software/dependencies_manual.pdf>`_
    allows explicit specification of the root dependency, e.g. `root(ROOT-0, makes-8)`.
    However, this is not allowed by Brat, so this writer does not print it.

    UD v2.0 allows tokens with spaces, but I am not aware of any Brat support.

    Alternatives:

    * `write.Conllu` Brat recently supports also the CoNLL-U input
    * `write.TextModeTrees` may be more readable/useful in some usecases
    * `write.Html` dtto, press "Save as SVG" button, convert to pdf
    """

    def __init__(self, print_upos=True, print_feats=False, always_ord=False, **kwargs):
        """Create the Sdparse block object.

        Args:
        print_upos: include UPOS tags (separated by / from forms) (default=True)
        print_feats: include FEATS (attached to upos in square brackets) (default=False)
        always_ord: attach word-order index to all forms in dependencies, even if not necessary
        """
        super().__init__(**kwargs)
        self.print_upos = print_upos
        self.print_feats = print_feats
        self.always_ord = always_ord

    def process_tree(self, tree):
        print(r'~~~ sdparse')

        # Print the line with forms and optional upos tags and feats.
        nodes = tree.descendants
        print(' '.join(self._node(n) for n in nodes))

        # Print dependencies.
        forms = collections.Counter()
        if not self.always_ord:
            for node in nodes:
                forms[node.form] += 1
        for node in nodes:
            if not node.parent.is_root():
                gov = self._form(node.parent, forms)
                dep = self._form(node, forms)
                print('%s(%s, %s)' % (node.deprel, gov, dep))

        print('~~~')
        print('')

    @staticmethod
    def _escape(string):
        return string.replace('\\', '\\\\').replace('/', '\\/')

    def _form(self, node, forms):
        if self.always_ord or forms[node.form] > 1:
            return self._escape('%s-%d' % (node.form, node.ord))
        return self._escape(node.form)

    def _node(self, node):
        string = self._escape(node.form)
        if self.print_upos:
            string += '/' + node.upos
        if self.print_feats:
            feats = str(node.feats)
            if feats != '_':
                if not self.print_upos:
                    string += '/'
                string += '[%s]' % feats
        return string
