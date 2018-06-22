"""Html class is a writer for HTML+JavaScript+SVG visualization of dependency trees."""
from udapi.core.basewriter import BaseWriter


class Html(BaseWriter):
    """A writer for HTML+JavaScript+SVG visualization of dependency trees.

    .. code-block:: bash

      # from the command line
      udapy write.Html < file.conllu > file.html
      firefox file.html

    For offline use, we need to download first three JavaScript libraries::

      wget https://code.jquery.com/jquery-2.1.4.min.js
      wget https://cdn.rawgit.com/eligrey/FileSaver.js/1.3.4r/FileSaver.min.js
      wget https://cdn.rawgit.com/ufal/js-treex-view/gh-pages/js-treex-view.js
      udapy write.Html path_to_js=. < file.conllu > file.html
      firefox file.html

    This writer produces an html file with drawings of the dependency trees
    in the document (there are buttons for selecting which bundle will be shown).
    Under each node its form, upos and deprel are shown.
    In the tooltip its lemma and (morphological) features are shown.
    After clicking the node, all other attributes are shown.
    When hovering over a node, the respective word in the (plain text) sentence
    is highlighted. There is a button for downloading trees as SVG files.

    Three JavaScript libraries are required (jquery, FileSaver and js-treex-view).
    By default they are linked online (so Internet access is needed when viewing),
    but they can be also downloaded locally (so offline browsing is possible and
    the loading is faster): see the Usage example above.

    This block is based on `Treex::View <https://metacpan.org/release/Treex-View>`_
    but takes a different approach. `Treex::View` depends on (older version of)
    `Valence` (Perl interface to `Electron <https://electron.atom.io/>`_)
    and comes with a script `view-treex`, which takes a treex file,
    converts it to json behind the scenes (which is quite slow)
    and displays the json in a Valence window.

    This block generates the json code directly to the html file,
    so it can be viewed with any browser or even published online.
    (Most of the html file is actually the json.)

    When viewing the html file, the JavaScript library `js-treex-view`
    generates an svg on the fly from the json.
    """

    def __init__(self, path_to_js='web', **kwargs):
        """Create the writer.

        Arguments:
        * `path_to_js` path to jquery, FileSaver and js-treex-view.
          `web` means
          http://ufal.github.io/js-treex-view/js-treex-view.js,
          https://cdn.rawgit.com/eligrey/FileSaver.js/master/FileSaver.min.js and
          https://code.jquery.com/jquery-2.1.4.min.js
          will be linked.
          `path_to_js=.` means the libraries will be searched in the current directory.
        """
        super().__init__(**kwargs)
        self.path_to_js = path_to_js

    def process_document(self, doc):
        if self.path_to_js == 'web':
            jquery = 'https://code.jquery.com/jquery-2.1.4.min.js'
            fsaver = 'https://cdn.rawgit.com/eligrey/FileSaver.js/1.3.4/FileSaver.min.js'
            js_t_v = 'https://cdn.rawgit.com/ufal/js-treex-view/gh-pages/js-treex-view.js'
        else:
            jquery = self.path_to_js + '/jquery-2.1.4.min.js'
            fsaver = self.path_to_js + '/FileSaver.min.js'
            js_t_v = self.path_to_js + '/js-treex-view.js'

        print('<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">')
        print('<title>Udapi viewer</title>')  # TODO doc.loaded_from
        for js_file in (jquery, fsaver, js_t_v):
            print('<script src="%s"></script>' % js_file)
        print('</head>\n<body>')
        print('<button style="float:right" type="submit" onclick="saveTree()">'
              '<span>Save as SVG</span></button><div id="treex-view"></div><script>')
        print('data=[')
        for (bundle_number, bundle) in enumerate(doc, 1):
            # TODO: if not self._should_process_bundle(bundle): continue
            if bundle_number != 1:
                print(',', end='')
            print('{"zones":{', end='')
            first_zone = True
            desc = ''
            for tree in bundle.trees:
                # TODO: if not self._should_process_tree(tree): continue
                zone = tree.zone
                if first_zone:
                    first_zone = False
                else:
                    print(',', end='')
                print('"%s":{"sentence":"%s",' % (zone, _esc(tree.text)), end='')
                print('"trees":{"a":{"language":"%s","nodes":[' % zone)
                print('{"id":%s,"parent":null,' % _id(tree), end='')
                print('"firstson":' + _id(tree.children[0] if tree.children else None), end=',')
                print('"labels":["zone=%s","id=%s"]}' % (zone, tree.address()))
                desc += ',["[%s]","label"],[" ","space"]' % zone
                for node in tree.descendants:
                    desc += self.print_node(node)
                desc += r',["\n","newline"]'
                print(']}}}')
            # print desc without the extra starting comma
            print('},"desc":[%s]}' % desc[1:])
        print('];')
        print("$('#treex-view').treexView(data);")
        print('''function saveTree() {
         var svg_el = jQuery('svg');
         if (svg_el.length) {
            var svg = new Blob([svg_el.parent().html()], {type: "image/svg+xml"});
            saveAs(svg, 'tree.svg');
         }
        }''')
        print('</script></body></html>')

    @staticmethod
    def print_node(node):
        """JSON representation of a given node."""
        # pylint does not understand `.format(**locals())` and falsely alarms for unused vars
        # pylint: disable=too-many-locals,unused-variable
        names = ['ord', 'misc', 'form', 'lemma', 'upos', 'xpos', 'feats', 'deprel']
        values = node.get_attrs(names, undefs='')
        order, misc, form, lemma, upos, xpos, feats, deprel = [_esc(x) for x in values]
        address = node.address()
        id_node, id_parent = _id(node), _id(node.parent)
        firstson = node.children[0] if node.children else None
        rbrother = next((n for n in node.parent.children if node.precedes(n)), None)
        firstson_str = '"firstson":%s,' % _id(firstson) if firstson else ''
        rbrother_str = '"rbrother":%s,' % _id(rbrother) if rbrother else ''
        multiline_feats = feats.replace('|', r'\n')
        print(',{{"id":{id_node},"parent":{id_parent},"order":{order},{firstson_str}{rbrother_str}'
              '"data":{{"ord":{order},"form":"{form}","lemma":"{lemma}","upos":"{upos}",'
              '"xpos":"{xpos}","feats":"{feats}","deprel":"{deprel}",'  # TODO: deps
              '"misc":"{misc}","id":"{address}"}},'
              '"labels":["{form}","#{{#bb0000}}{upos}","#{{#0000bb}}{deprel}"],'
              '"hint":"lemma={lemma}\\n{multiline_feats}"}}'.format(**locals()))
        desc = ',["{form}",{id_node}]'.format(**locals())
        desc += ',[" ","space"]' if 'SpaceAfter=No' not in misc else ''
        # pylint: enable=too-many-locals,unused-variable
        return desc


# id needs to be a valid DOM querySelector
# so it cannot contain # nor / and it cannot start with a digit
def _id(node):
    if node is None:
        return 'null'
    return '"n%s"' % node.address().replace('#', '-').replace('/', '-')


def _esc(string):
    if string is None:
        string = ''
    return string.replace('\\', '\\\\').replace('"', r'\"')
