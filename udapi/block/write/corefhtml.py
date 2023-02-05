"""CorefHtml class is a writer for HTML+JavaScript visualization of coreference."""
from udapi.core.basewriter import BaseWriter
from udapi.core.coref import span_to_nodes, CorefEntity, CorefMention
from collections import Counter
import udapi.block.write.html

ETYPES = 'person place organization animal plant object substance time number abstract event'.split()

CSS = '''
.sentence span {border: 1px solid black; border-radius: 5px; padding: 2px; display:inline-block;}
.sentence span .eid {display:block; font-size: 10px;}
.showtree {float:left; margin: 5px;}
.close{float:right; font-weight: 900; font-size: 30px; width: 36px; height: 36px; padding: 2px}
.empty {color: gray;}
.sentence .singleton {border-style: dotted;}
.crossing:before {content: "!"; display: block; background: #ffd500;}
.active {border: 1px solid red !important;}
.selected {background: red !important; text-shadow: 1px 1px 4px white, -1px 1px 4px white, 1px -1px 4px white, -1px -1px 4px white;}
.other {background: hsl(0, 0%, 85%);}
'''

SCRIPT_BASE = '''
$("span").click(function(e) {
 let was_selected = $(this).hasClass("selected");
 $("span").removeClass("selected");
 if (!was_selected){$("."+$(this).attr("class").split(" ")[0]).addClass("selected");}
 e.stopPropagation();
});

$("span").hover(
 function(e) {$("span").removeClass("active"); $("."+$(this).attr("class").split(" ")[1]).addClass("active");},
 function(e) {$("span").removeClass("active");}
);
'''

SCRIPT_SHOWTREE = '''
$(".sentence").each(function(index){
  var sent_id = this.id;
  $(this).before(
    $("<button>", {append: "🌲", id:"button-"+sent_id, title: "show dependency tree", class: "showtree"}).on("click", function() {
      var tree_div = $("#tree-"+sent_id);
      if (tree_div.length == 0){
        var tdiv = $("<div>", {id:"tree-"+sent_id}).insertBefore($(this));
        tdiv.treexView([data[index]]);
        $("<button>",{append:"×", class:"close"}).prependTo(tdiv).on("click", function(){$(this).parent().remove();});
        $('#button-'+sent_id).attr('title', 'hide dependency tree');
      } else {tree_div.remove();}
    })
  );
});
'''

class CorefHtml(BaseWriter):

    def __init__(self, show_trees=True, show_eid=True, colors=7, **kwargs):
        super().__init__(**kwargs)
        self.show_trees = show_trees
        self.show_eid = show_eid
        self.colors = colors

    def process_document(self, doc):
        print('<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">')
        print('<title>Udapi CorefUD viewer</title>')
        print('<script src="https://code.jquery.com/jquery-3.6.3.min.js"></script>')
        if self.show_trees:
            print('<script src="https://cdn.rawgit.com/ufal/js-treex-view/gh-pages/js-treex-view.js"></script>')
        print('<style>' + CSS)
        for i, etype in enumerate(ETYPES):
            print(f'.{etype} {{background: hsl({int(i * 360/len(ETYPES))}, 80%, 85%);}}')
        if self.colors:
            for i in range(self.colors):
                print(f'.c{i} {{color: hsl({int(i * 360/self.colors)}, 100%, 30%);}}')
        print('</style>')
        print('</head>\n<body>')

        mention_ids = {}
        entity_colors = {}
        entities_of_type = Counter()
        for entity in doc.coref_entities:
            if self.colors:
                count = entities_of_type[entity.etype]
                entities_of_type[entity.etype] = count + 1
                entity_colors[entity] = f'c{count % self.colors}'
            for idx, mention in enumerate(entity.mentions, 1):
                mention_ids[mention] = f'{entity.eid}e{idx}'

        for tree in doc.trees:
            self.process_tree(tree, mention_ids, entity_colors)

        print('<script>')
        print(SCRIPT_BASE)
        if self.show_trees:
            print('data=[')
            for (bundle_number, bundle) in enumerate(doc, 1):
                if bundle_number != 1:
                    print(',', end='')
                print('{"zones":{', end='')
                first_zone = True
                desc = ''
                for tree in bundle.trees:
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
                        desc += udapi.block.write.html.Html.print_node(node)
                    desc += r',["\n","newline"]'
                    print(']}}}')
                # print desc without the extra starting comma
                print('},"desc":[%s]}' % desc[1:])
            print('];')
            print(SCRIPT_SHOWTREE)
        print('</script>')
        print('</body></html>')

    def _start_subspan(self, subspan, mention_ids, entity_colors, crossing=False):
        m = subspan.mention
        e = m.entity
        classes = f'{e.eid} {mention_ids[m]} {e.etype or "other"}'
        title = f'eid={subspan.subspan_eid}\ntype={e.etype} ({entity_colors[e]})\nhead={m.head.form}'
        if self.colors:
            classes += f' {entity_colors[e]}'
        if all(w.is_empty() for w in subspan.words):
            classes += ' empty'
        if len(e.mentions) == 1:
            classes += ' singleton'
        if crossing:
            classes += ' crossing'
            title += '\ncrossing'
        if m.other:
            title += f'\n{m.other}'
        print(f'<span class="{classes}" title="{title}">', end='')
        if self.show_eid:
            print(f'<b class="eid">{subspan.subspan_eid}</b>', end='')

    def process_tree(self, tree, mention_ids, entity_colors):
        mentions = set()
        nodes_and_empty = tree.descendants_and_empty
        for node in nodes_and_empty:
            for m in node.coref_mentions:
                mentions.add(m)

        subspans = []
        for mention in mentions:
            subspans.extend(mention._subspans())
        subspans.sort(reverse=True)

        if tree.newdoc:
            print(f'<hr><h1>{tree.newdoc if tree.newdoc is not True else ""}</h1><hr>')
        elif tree.newpar:
            print('<hr>')
        opened = []
        print(f'<p class="sentence" id={_id(tree)}>')
        for node in nodes_and_empty:
            while subspans and subspans[-1].words[0] == node:
                subspan = subspans.pop()
                self._start_subspan(subspan, mention_ids, entity_colors)
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

            # Two mentions are crossing iff their spans have non-zero intersection,
            # but neither is a subset of the other, e.g. (e1 ... (e2 ... e1) ... e2).
            # Let's visualize this (simplified) as
            # <span class=e1>...<span class=e2>...</span></span><span class="e2 crossing">...</span>
            # i.e. let's split mention e2 into two subspans which are next to each other.
            # Unfortunatelly, we cannot mark now both crossing mentions using html class "crossing"
            # (opening tags are already printed), so we'll mark only the second part of the second mention.
            endings = [x for x in opened if x.words[-1] == node]
            if endings:
                new_opened, brokens, found_crossing = [], [], False
                for subspan in opened:
                    if subspan.words[-1] == node:
                        found_crossing = True
                    elif found_crossing:
                        brokens.append(subspan)
                    else:
                        new_opened.append(subspan)
                opened = new_opened
                print('</span>' * (len(endings) + len(brokens)), end='')
                for broken in brokens:
                    self._start_subspan(broken, mention_ids, entity_colors, True)
                    opened.append(subspan)

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
