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

        sent_mentions = []
        for mention in mentions:
            mspan = mention.span
            if ',' not in mspan:
                sent_mentions.append(mention)
            else:
                entity = mention.entity
                head_str = str(mention.words.index(mention.head) + 1)
                subspans = mspan.split(',')
                for idx,subspan in enumerate(subspans, 1):
                    subspan_eid = f'{entity.eid}[{idx}/{len(subspans)}]'
                    subspan_words = span_to_nodes(tree, subspan)
                    fake_entity = CorefEntity(subspan_eid, entity.etype)
                    fake_mention = CorefMention(subspan_words, head_str, fake_entity, add_word_backlinks=False)
                    if mention._other:
                        fake_mention._other = mention._other
                    if mention._bridging and idx == 1:
                        fake_mention._bridging = mention._bridging
                    sent_mentions.append(fake_mention)
        sent_mentions.sort(reverse=True)

        opened = []
        print('<p>')
        for node in nodes_and_empty:
            while sent_mentions and sent_mentions[-1].words[0] == node:
                m = sent_mentions.pop()
                e = m.entity
                classes = f'{e.eid} {e.etype or "other"}'
                if all(w.is_empty() for w in m.words):
                    classes += ' empty'
                if len(e.mentions) == 1:
                    classes += ' singleton'
                title = f'eid={e.eid}\ntype={e.etype}\nhead={m.head.form}'
                print(f'<span class="{classes}" data-eid="{e.eid}" title="{title}"', end='')
                if m.other:
                    print(f'\n{m.other}', end='')
                print('">', end='')
                opened.append(m)
            
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
