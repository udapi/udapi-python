"""CorefHtml class is a writer for HTML+JavaScript visualization of coreference."""
from udapi.core.basewriter import BaseWriter
from udapi.core.coref import span_to_nodes, CorefEntity, CorefMention

ETYPES = 'person place organization animal plant object substance time number abstract event'.split()

class CorefHtml(BaseWriter):

    def __init__(self, path_to_js='web', **kwargs):
        super().__init__(**kwargs)
        self.path_to_js = path_to_js

    def process_document(self, doc):
        print('<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">')
        print('<title>Udapi CorefUD viewer</title>')
        print('<script src="https://code.jquery.com/jquery-3.6.3.min.js"></script>')
        #print('<script src="coref.js"></script>') #$(window).on("load", function() {...}
        #print('<link rel="stylesheet" href="coref.css">')
        print('<style>\n'
              'span {border: 1px solid black; border-radius: 5px; padding: 2px; display:inline-block;}\n'
              '.empty {color: gray;}\n'
              '.singleton {color: rgb(0,0,100);}\n'
              '.selected {background: red !important;}\n'
              '.other{ background: hsl(0, 0%, 85%);}')
        for i, etype in enumerate(ETYPES):
            print(f'.{etype}{{background: hsl({int(i * 360/len(ETYPES))}, 80%, 85%);}}')
        print('</style>')
        print('</head>\n<body>')

        for tree in doc.trees:
            self.process_tree(tree)

        print('<script>\n$("span").click(function(e) {\n'
              ' let was_selected = $(this).hasClass("selected");\n'
              ' $("span").removeClass("selected");\n'
              ' if (!was_selected){$("."+$(this).attr("class").split(" ")[0]).addClass("selected");}\n'
              ' e.stopPropagation();\n});\n</script>')
        print('</body></html>')

    def process_tree(self, tree):
        mentions = set()
        nodes_and_empty = tree.descendants_and_empty
        for node in nodes_and_empty:
            for m in node.coref_mentions:
                mentions.add(m)

        subspans = []
        for mention in mentions:
            subspans.extend(mention._subspans())
        subspans.sort(reverse=True)

        opened = []
        print('<p>')
        for node in nodes_and_empty:
            while subspans and subspans[-1].words[0] == node:
                subspan = subspans.pop()
                m = subspan.mention
                e = m.entity
                classes = f'{e.eid} {e.etype or "other"}'
                if all(w.is_empty() for w in subspan.words):
                    classes += ' empty'
                if len(e.mentions) == 1:
                    classes += ' singleton'

                title = f'eid={subspan.subspan_eid}\ntype={e.etype}\nhead={m.head.form}'
                if m.other:
                    title += f'\n{m.other}'
                print(f'<span class="{classes}" title="{title}">', end='') #data-eid="{e.eid}"

                opened.append(subspan)
            
            is_head = self._is_head(node)
            if is_head:
                print('<b>', end='')
            if node.is_empty():
                print('<i>', end='')
            print(node.form, end='')
            if node.is_empty():
                print('</i>', end='')
            if is_head:
                print('</b>', end='')
            
            while opened and opened[-1].words[-1] == node:
                print('</span>', end='')
                opened.pop()

            if not node.no_space_after:
                print(' ', end='')
                
        print('</p>')

    def _is_head(self, node):
        for mention in node.coref_mentions:
            if mention.head == node:
                return mention
        return None

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
