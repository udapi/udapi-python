"""Vislcg class is a writer for the VISL-cg format."""
from udapi.core.basewriter import BaseWriter

# https://dev.w3.org/html5/html-author/charref
ESCAPE_TABLE = {
    '§': '§sect.',
    '"': '§quot.',
    '#': '§num.',
    ';': '§semi.',
    '=': '§equals.',
    '(': '§lpar.',
    ')': '§rpar.',
    '|': '§verbar.',
}


class Vislcg(BaseWriter):
    """A writer of files in the VISL-cg format, suitable for VISL Constraint Grammer Parser.

    See https://visl.sdu.dk/visl/vislcg-doc.html

    Usage:
    ``udapy write.Vislcg < in.conllu > out.vislcg``

    Example output::

      "<Қыз>"
              "қыз" n nom @nsubj #1->3
      "<оның>"
              "ол" prn pers p3 sg gen @nmod:poss #2->3
      "<қарындасы>"
              "қарындас" n px3sp nom @parataxis #3->8
                  "е" cop aor p3 sg @cop #4->3
      "<,>"
              "," cm @punct #5->8
      "<ол>"
              "ол" prn pers p3 sg nom @nsubj #6->8
      "<бес>"
              "бес" num @nummod #7->8
      "<жаста>"
              "жас" n loc @root #8->0
                  "е" cop aor p3 sg @cop #9->8
      "<.>"
              "." sent @punct #10->8

    Example input::

      # text = Қыз оның қарындасы, ол бес жаста.
      1    Қыз        қыз       _  n     nom             3  nsubj      _  _
      2    оның       ол        _  prn   pers|p3|sg|gen  3  nmod:poss  _  _
      3-4  қарындасы  _         _  _     _               _  _          _  _
      3    қарындасы  қарындас  _  n     px3sp|nom       8  parataxis  _  _
      4    _          е         _  cop   aor|p3|sg       3  cop        _  _
      5    ,          ,         _  cm    _               8  punct      _  _
      6    ол         ол        _  prn   pers|p3|sg|nom  8  nsubj      _  _
      7    бес        бес       _  num   _               8  nummod     _  _
      8-9  жаста      _         _  _     _               _  _          _  _
      8    жаста      жас       _  n     loc             0  root       _  _
      9    _          е         _  cop   aor|p3|sg       8  cop        _  _
      10   .          .         _  sent  _               8  punct      _  _
    """

    def process_tree(self, tree):
        # Print the line with forms and optional upos tags and feats.
        for token in tree.token_descendants:
            print('"<%s>"' % self._escape(token.form))
            try:
                words = token.words
            except AttributeError:
                words = [token]
            print('\t' + self._node(words[0]))
            for nonfirst_mwt_word in words[1:]:
                print('\t\t' + self._node(nonfirst_mwt_word))
        print('')

    @staticmethod
    def _escape(string):
        return ''.join(ESCAPE_TABLE.get(c, c) for c in string)

    def _node(self, node):
        attrs = ['"%s"' % self._escape(node.lemma)]
        attrs.append(self._escape(node.xpos))
        feats = str(node.feats).replace('|', ' ')
        if feats != '_':
            attrs.append(self._escape(feats))
        attrs.append('@' + node.deprel)
        attrs.append('#%d->%d' % (node.ord, node.parent.ord))
        return ' '.join(attrs)
