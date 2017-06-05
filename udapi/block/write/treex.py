"""write.Treex is a writer block for Treex XML (e.g. for TrEd editing)."""
from udapi.core.basewriter import BaseWriter


class Treex(BaseWriter):
    """A writer of files in the Treex format."""

    def before_process_document(self, doc):
        super().before_process_document(doc)
        print('<?xml version="1.0" encoding="UTF-8"?>\n'
              '<treex_document xmlns="http://ufal.mff.cuni.cz/pdt/pml/">\n'
              '  <head>\n'
              '    <schema href="treex_schema.xml" />\n'
              '  </head>\n'
              '  <meta/>\n'
              '  <bundles>')

    def after_process_document(self, doc):
        print("  </bundles>\n</treex_document>\n")
        super().after_process_document(doc)

    def process_bundle(self, bundle):
        print('    <LM id="%s">\n      <zones>' % bundle.bundle_id)
        super().process_bundle(bundle)
        print('      </zones>\n    </LM>')

    def process_tree(self, tree):
        zone_parts = tree.zone.split('_')
        language, selector = zone_parts if len(zone_parts) == 2 else ('und', tree.zone)
        tree_id = tree.bundle.bundle_id + '-' + language
        ind = ' ' * 8
        print(ind + "<zone language='%s' selector='%s'>" % (language, selector))
        if tree.text:
            print(ind + "  <sentence>%s</sentence>" % tree.text)
        print(ind + "  <trees>\n" + ind + "    <a_tree id='%s'>" % tree_id)
        self.print_subtree(tree, tree_id, ' ' * 12)
        print(ind + "    </a_tree>\n" + ind + "  </trees>\n" + ind + "</zone>")

    def print_subtree(self, node, tree_id, indent):
        """Recrsively print trees in Treex format."""
        if not node.is_root():
            print(indent + "<LM id='%s-n%s'>" % (tree_id, node.ord))
        ind = indent + '  '
        print(ind + "<ord>%s</ord>" % node.ord)
        if not node.is_root():
            if node.form:
                print(ind + "<form>%s</form>" % node.form)
            if node.lemma:
                print(ind + "<lemma>%s</lemma>" % node.lemma)
            if node.upos:
                print(ind + "<tag>%s</tag>" % node.upos)
            if node.deprel:
                print(ind + "<deprel>%s</deprel>" % node.deprel)
            print(ind + "<conll><pos>%s</pos><feat>%s</feat></conll>"
                  % (node.xpos, str(node.feats)))

        # TODO misc and deps into wild, but probably need to encode ř as \x{159} etc.
        if node.children:
            print(ind + "<children>")
            for child in node. children:
                self.print_subtree(child, tree_id, ind + '  ')
            print(ind + "</children>")
        if not node.is_root():
            print(indent + "</LM>")
