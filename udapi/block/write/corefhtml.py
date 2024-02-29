"""CorefHtml class is a writer for HTML+JavaScript visualization of coreference.

When using lazy loading of documents (infinite scrolling),
modern browsers don't allow JavaScript to load files from a local file system
("Access to XMLHttpRequest at 'file://.../doc2.html' from origin 'null' has been
blocked by CORS policy: Cross origin requests are only supported for protocol schemes:
http, data, chrome, chrome-extension, https.")

The recommended solution is to start a local web server, e.g. using
  python -m http.server
and browse http://0.0.0.0:8000/my.html.

Non-recommended solution is to run
 google-chrome --new-window --user-data-dir=/tmp/chrome-proxy --allow-file-access-from-files my.html
"""
from udapi.core.basewriter import BaseWriter
from udapi.core.coref import span_to_nodes, CorefEntity, CorefMention
from collections import Counter
import udapi.block.write.html
import gzip
import sys
import os
import re

ETYPES = 'person place organization animal plant object substance time number abstract event'.split()

HTYPES = 'PROPN NOUN PRON VERB DET OTHER'.split()

HEADER = '''
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<title>Udapi CorefUD viewer</title>
<script src="https://code.jquery.com/jquery-3.6.3.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/pako/2.1.0/pako.min.js"></script>
'''

CSS = '''
#wrap {display: flex; align-items: flex-start;}
#main {width: 100%; padding: 5px; background: white; z-index:100;}
#overview { position: sticky; top: 0; overflow-y: scroll; height:95vh; resize:horizontal;
            display: grid; border-right: double;
            padding: 5px; width: 20em; background: #ddd; border-radius: 5px;
}
#main-menu {position:fixed; z-index:150; top: 4px; right:4px; display:none;
            padding: 5px 55px 5px 5px; background-color:gray; border-radius: 5px;}
#main-menu div {display: inline-block;}
#menubtn {position: fixed; right: 8px; top: 8px; z-index: 200;}
#menubtn div {width: 30px; height: 4px; background-color: black; margin: 5px 0; transition: 0.4s;}
.change .b1 {transform: translate(0, 9px) rotate(-45deg);}
.change .b2 {opacity: 0;}
.change .b3 {transform: translate(0, -9px) rotate(45deg);}

.m {border: 1px solid black; border-radius: 5px; padding: 2px; display:inline-block;}
.nobox {border:1px solid transparent; padding:0; background: transparent !important; display: inline}
.nobox .labels {display: inline;}
.nocolor {color: black !important;}
.nobold {font-weight: normal;}
.labels {display: block; font-size: 10px;}
.showtree {margin: 5px; user-select: none;}
.display-inline {display: inline;}
.close{float:right; font-weight: 900; font-size: 30px; width: 36px; height: 36px; padding: 2px}
i.empty {color: gray; border: 3px outset gray; padding: 1px;}
.sentence .singleton {border-style: dotted;}
.crossing:before {content: "!"; display: block; background: #ffd500;}
.active {border: 1px solid red !important;}
.selected {background: red !important; text-shadow: 1px 1px 4px white, -1px 1px 4px white, 1px -1px 4px white, -1px -1px 4px white;}
.sent_id {display: none; background: #ddd; border-radius: 3px;}
'''

SCRIPT_BASE = '''
function add_mention_listeners(mentions){
 mentions.click(function(e) {
   let was_selected = $(this).hasClass("selected");
   $(".m").removeClass("selected");
   if (!was_selected) {$("."+$(this).attr("class").split(" ")[0]).addClass("selected");}
   e.stopPropagation();
  });
 mentions.hover(
   function(e) {$(".m").removeClass("active"); $("."+$(this).attr("class").split(" ")[1]).addClass("active");},
   function(e) {$(".m").removeClass("active");}
  );
}
add_mention_listeners($(".m"));

window.onhashchange = function() {
 $(".m").removeClass("selected");
 var fragment = window.location.hash.substring(1);
 if (fragment) {$("." + fragment).addClass("selected");}
}

function menuclick(x) {
  x.classList.toggle("change");
  $("#main-menu").toggle();
}

async function load_doc(doc_num) {
  loading_now = true;
  let filename = docs_dir + "/doc" + doc_num + ".html.gz"
  console.log("loading " + filename);
  try {
    const res = await fetch(filename);
    let raw = await res.arrayBuffer();
    data = pako.inflate(raw, {to: "string"});
  } catch (error){
    if (! load_fail_reported) {
      load_fail_reported = true;
      alert("Cannot load " + filename + "\\nLocal files do not support lazy loading."
      + " Run a web server 'python -m http.server'\\n"
      + "error = " + error);
    }
  }
  $("#main").append(data);
  add_mention_listeners($("#doc" + doc_num + " .m"));
  $("#doc" + doc_num + " .sentence").each(add_show_tree_button);
  $('.eid').toggle($('#show-eid')[0].checked);
  $('.etype').toggle($('#show-etype')[0].checked);
  $('.sent_id').toggle($('#show-sent_id')[0].checked);
  $('.showtree').toggle($('#show-trees')[0].checked);
  $('.m').toggleClass('nocolor', ! $('#show-color')[0].checked);
  $('.m').toggleClass('nobox', ! $('#show-boxes')[0].checked);
  $('.norm').toggle($('#show-norm')[0].checked);
  $('.head').toggleClass('nobold', ! $('#show-heads')[0].checked);
  $('.empty').toggle($('#show-empty')[0].checked);
  $('.sentence').toggleClass('display-inline', ! $('#show-breaks')[0].checked);
  $('.par').toggle($('#show-pars')[0].checked);
  $('h1').toggle($('#show-docs')[0].checked);
  $('.m').toggleClass('htype',$('#htype')[0].checked)
  loading_now = false;
}

var docs_loaded = 1;
var load_fail_reported = false;
var loading_now = false;
add_show_tree_button = function(index, el){ // to be redefined later if show_trees=True
  $(el).prepend('<span class="sent_id">🆔' + el.dataset.id + '</span>');
}
function load_more() {
  if (!loading_now && $(window).scrollTop() >= $(document).height() - $(window).height() - 42 && docs_loaded < all_docs) {
    docs_loaded += 1;
    load_doc(docs_loaded);
  }
}
$(window).scroll(load_more);
const resizeObserver = new ResizeObserver(entries =>load_more());
resizeObserver.observe(document.body);
'''

SCRIPT_SHOWTREE = '''
function show_tree_in_tdiv(tdiv, doc_number, index){
  tdiv.treexView([docs_json[doc_number][index]]);
  $("<button>", {append:"×", class:"close"}).prependTo(tdiv).on("click", function(){tdiv.remove();});
}

var load_json_fail_reported = false;
add_show_tree_button = function(index, el){
  var sent_id = el.id;
  $(el).prepend('<span class="sent_id">🆔' + el.dataset.id + '</span>');
  $(el).prepend(
    $("<button>", {append: "🌲", id:"button-"+sent_id, title: "show dependency tree "+el.dataset.id, class: "showtree"}).on("click", async function() {
      var tree_div = $("#tree-"+sent_id);
      if (tree_div.length == 0){
        $('#button-'+sent_id).attr('title', 'hide dependency tree '+el.dataset.id);
        var tdiv = $("<div>", {id:"tree-"+sent_id, class:"tree"}).insertAfter($(el));
        doc_number = 1 * el.parentElement.id.substr(3);
        if (docs_json[doc_number]){
          show_tree_in_tdiv(tdiv, doc_number, index);
        } else {
          try {
            console.log("loading doc" + doc_number + ".json.gz");
            const res = await fetch(docs_dir + "/doc" + doc_number + ".json.gz");
            let raw = await res.arrayBuffer();
            docs_json[doc_number] = JSON.parse(pako.inflate(raw, {to: "string"}));
            show_tree_in_tdiv(tdiv, doc_number, index);
          } catch(error) {
            if (! load_json_fail_reported) {
              load_json_fail_reported = true;
              alert("Cannot load " + docs_dir + "/doc" + doc_number + ".json.gz:\\n" + error);
            }
          }
        }
      } else {
        tree_div.remove();
        $('#button-'+sent_id).attr('title', 'show dependency tree '+el.dataset.id);
      }
    })
  );
}
'''

WRITE_HTML = udapi.block.write.html.Html()

class CorefHtml(BaseWriter):

    def __init__(self, docs_dir='docs', path_to_js='web',
                 show_trees=True, show_eid=False, show_etype=False, colors=7, rtl=None, **kwargs):
        super().__init__(**kwargs)
        self.path_to_js = path_to_js
        self.show_trees = show_trees
        self.show_eid = show_eid
        self.show_etype = show_etype
        self.colors = colors
        self.rtl = rtl
        self.js_docs_dir = docs_dir
        self.docs_dir = docs_dir
        if self.path:
            new_dir, _ = os.path.split(self.path)
            self.docs_dir = os.path.join(new_dir, docs_dir)
        if docs_dir != '.' and not os.path.exists(self.docs_dir):
            os.makedirs(self.docs_dir)

        self._mention_ids = {}
        self._entity_colors = {}

    def _representative_word(self, entity):
        # return the first PROPN or NOUN. Or the most frequent one?
        heads = [m.head for m in entity.mentions]
        lemma_or_form = lambda n: n.lemma if n.lemma and n.lemma != '_' else n.form
        for upos in ('PROPN', 'NOUN'):
            nodes = [n for n in heads if n.upos == upos]
            if nodes:
                return lemma_or_form(nodes[0])
        return lemma_or_form(heads[0])

    def process_ud_doc(self, ud_doc, doc_num):
        print(f'<div class="doc" id="doc{doc_num}">')
        for tree in ud_doc:
            self.process_tree(tree)
        print('</div>')

    def process_document(self, doc):
        ud_docs, doc_num, sent_id2doc = [], 0, {}
        for tree in doc.trees:
            if tree.newdoc or not ud_docs:
                ud_docs.append([])
                doc_num += 1
            ud_docs[-1].append(tree)
            sent_id2doc[tree.sent_id] = doc_num
        # TODO: use sent_id2doc

        print('<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">')
        print('<title>Udapi CorefUD viewer</title>')
        if self.path_to_js == 'web':
            print('<script src="https://code.jquery.com/jquery-3.6.3.min.js"></script>')
            print('<script src="https://cdnjs.cloudflare.com/ajax/libs/pako/2.1.0/pako.min.js"></script>')
            if self.show_trees:
                print('<script src="https://cdn.rawgit.com/ufal/js-treex-view/gh-pages/js-treex-view.js"></script>')
        else:
            print(f'<script src="{self.path_to_js}/jquery-3.6.3.min.js"></script>')
            print(f'<script src="{self.path_to_js}/pako.min.js"></script>')
            if self.show_trees:
                print(f'<script src="{self.path_to_js}/js-treex-view.js"></script>')
        print('<style>' + CSS)
        for i, etype in enumerate(ETYPES):
            print(f'.{etype} {{background: hsl({int(i * 360/len(ETYPES))}, 80%, 85%);}}')
        print('.other {background: hsl(0, 0%, 85%);}')
        for i, htype in enumerate(HTYPES[:-1]):
            print(f'.htype.{htype} {{background: hsl({int(i * 360/len(HTYPES))}, 80%, 85%);}}')
        print('.htype.OTHER {background: hsl(0, 0%, 85%);}')
        if self.colors:
            for i in range(self.colors):
                print(f'.c{i} {{color: hsl({int(i * 360/self.colors)}, 100%, 30%);}}')
        if not self.show_eid:
            print('.eid {display: none;}')
        if not self.show_etype:
            print('.etype {display: none;}')
        print('</style>')
        print('</head>\n<body>\n<div id="wrap">')

        self._mention_ids = {}
        self._entity_colors = {}
        entities_of_type = Counter()
        for entity in doc.coref_entities:
            if self.colors:
                count = entities_of_type[entity.etype]
                entities_of_type[entity.etype] = count + 1
                self._entity_colors[entity] = f'c{count % self.colors}'
            for idx, mention in enumerate(entity.mentions, 1):
                self._mention_ids[mention] = f'{_dom_esc(entity.eid)}e{idx}'

        print('<div id="overview">')
        print('<table><thead><tr><th title="entity id">eid</th>'
              '<th title="number of mentions">#m</th>'
              '<th title="a word best representing the entity">word</th></tr></thead>\n<tbody>')
        for entity in doc.coref_entities:
            print(f'<tr><td><a href="#{_dom_esc(entity.eid)}">{entity.eid}</a></td>'
                  f'<td>{len(entity.mentions)}</td>'
                  f'<td>{self._representative_word(entity)}</td></tr>')
        print('</tbody></table>')
        print('</div>')

        print('<div id="main">')
        print('<div id="main-menu">Show<br><div>\n'
              f' <input id="show-eid" type="checkbox" {"checked" if self.show_eid else ""} onclick="$(\'.eid\').toggle(this.checked);"><label for="show-eid">eid</label><br>\n'
              f' <input id="show-etype" type="checkbox" {"checked" if self.show_etype else ""} onclick="$(\'.etype\').toggle(this.checked);"><label for="show-etype">etype</label><br>\n'
              ' <input id="show-sent_id" type="checkbox" onclick="$(\'.sent_id\').toggle(this.checked);"><label for="show-sent_id">sent_id</label><br>\n'
              + (' <input id="show-trees" type="checkbox" checked onclick="$(\'.showtree\').toggle(this.checked);"><label for="show-trees">trees</label><br>\n' if self.show_trees else '') +
              ' <input id="show-color" type="checkbox" checked onclick="$(\'.m\').toggleClass(\'nocolor\',!this.checked);"><label for="show-color">colors</label><br>\n'
              ' <input id="show-boxes" type="checkbox" checked onclick="$(\'.m\').toggleClass(\'nobox\',!this.checked);"><label for="show-boxes">boxes</label></div><div>\n'
              ' <input id="show-norm" type="checkbox" checked onclick="$(\'.norm\').toggle(this.checked);"><label for="show-norm">non-mentions</label><br>\n'
              ' <input id="show-heads" type="checkbox" checked onclick="$(\'.head\').toggleClass(\'nobold\',!this.checked);"><label for="show-heads">heads in bold</label><br>\n'
              ' <input id="show-empty" type="checkbox" checked onclick="$(\'.empty\').toggle(this.checked);"><label for="show-empty">empty words</label><br>\n'
              ' <input id="show-breaks" type="checkbox" checked onclick="$(\'.sentence\').toggleClass(\'display-inline\',!this.checked);"><label for="show-breaks">sentence per line</label><br>\n'
              ' <input id="show-pars" type="checkbox" checked onclick="$(\'.par\').toggle(this.checked);"><label for="show-pars">paragraphs</label><br>\n'
              ' <input id="show-docs" type="checkbox" checked onclick="$(\'h1\').toggle(this.checked);"><label for="show-docs">document names</label><br>\n'
              '</div><fieldset onclick="$(\'.m\').toggleClass(\'htype\',$(\'#htype\')[0].checked)"><legend>bg color:</legend>\n'
              '<label><input type="radio" name="bgcolor" id="etype" checked>entity type</label>\n'
              '<label><input type="radio" name="bgcolor" id="htype">head upos</label>\n'
              '</fieldset>\n'
              '</div>\n'
              '<button id="menubtn" title="Visualization options" onclick="menuclick(this)"><div class="b1"></div><div class="b2"></div><div class="b3"></div></button>\n'
              )

        # The first ud_doc will be printed to the main html file.
        self.process_ud_doc(ud_docs[0], 1)
        print('</div>') # id=main

        # Other ud_docs will be printed into separate files (so they can be loaded lazily)
        orig_stdout = sys.stdout
        try:
            for i, ud_doc in enumerate(ud_docs[1:], 2):
                sys.stdout = gzip.open(f"{self.docs_dir}/doc{i}.html.gz", 'wt')
                self.process_ud_doc(ud_doc, i)
                sys.stdout.close()
        finally:
            sys.stdout = orig_stdout

        print(f'<script>\nvar all_docs = {len(ud_docs)};\nvar docs_dir = "{self.js_docs_dir}";')
        print(SCRIPT_BASE)
        if self.show_trees:
            print('docs_json = [false, ', end='') # 1-based index, so dummy docs_json[0]
            WRITE_HTML.print_doc_json(ud_docs[0])
            print('];')
            try:
                for i, ud_doc in enumerate(ud_docs[1:], 2):
                    sys.stdout = gzip.open(f"{self.docs_dir}/doc{i}.json.gz", 'wt')
                    WRITE_HTML.print_doc_json(ud_doc)
                    sys.stdout.close()
            finally:
                sys.stdout = orig_stdout
            print(SCRIPT_SHOWTREE)
        print('$("#doc1 .sentence").each(add_show_tree_button);')
        print('</script>')
        print('</div></body></html>')

    def _start_subspan(self, subspan, crossing=False):
        m = subspan.mention
        e = m.entity
        classes = f'{_dom_esc(e.eid)} {self._mention_ids[m]} {e.etype or "other"} m'
        title = f'eid={subspan.subspan_eid}\netype={e.etype}\nhead={m.head.form}'
        classes += f" {m.head.upos if m.head.upos in HTYPES else 'OTHER'}"
        title += f'\nhead-upos={m.head.upos}'
        if self.colors:
            classes += f' {self._entity_colors[e]}'
        if all(w.is_empty() for w in subspan.words):
            classes += ' empty'
        if len(e.mentions) == 1:
            classes += ' singleton'
        if crossing:
            classes += ' crossing'
            title += '\ncrossing'
        if m.other:
            title += f'\n{m.other}'
        span_id = ''
        if (subspan.subspan_id == '' or subspan.subspan_id.startswith('[1/')) and e.mentions[0] == m:
            span_id = f'id="{_dom_esc(e.eid)}" '
        # The title should be always rendered left-to-right (e.g. "head=X", not "X=head"),
        # so for RTL languages, we need to use explicit dir="ltr" and insert a nested span with dir="rtl".
        if self.rtl:
            print(f'<span {span_id}class="{classes}" title="{title}" dir="ltr">'
                  f'<span class="labels"><b class="eid">{_dom_esc(subspan.subspan_eid)}</b>'
                  f' <i class="etype">{e.etype}</i></span><span dir="rtl">', end='')
        else:
            print(f'<span {span_id}class="{classes}" title="{title}">'
                  f'<span class="labels"><b class="eid">{_dom_esc(subspan.subspan_eid)}</b>'
                  f' <i class="etype">{e.etype}</i></span>', end='')

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

        if tree.newdoc:
            print(f'<hr><h1>{tree.newdoc if tree.newdoc is not True else ""}</h1><hr>')
        elif tree.newpar:
            print('<hr class="par">')
        opened, prev_node_mention = [], True
        rtl = ' dir="rtl"' if self.rtl else ""
        print(f'<p class="sentence" data-id="{tree.sent_id}" id="{_id(tree)}"{rtl}>')
        for node in nodes_and_empty:
            if not prev_node_mention and subspans and subspans[-1].words[0] == node:
                print('</span>', end='')
            while subspans and subspans[-1].words[0] == node:
                subspan = subspans.pop()
                self._start_subspan(subspan)
                opened.append(subspan)

            if not opened and prev_node_mention:
                print('<span class="norm">', end='')
            prev_node_mention = True if opened else False
            is_head = self._is_head(node)
            if is_head:
                print('<b class="head">', end='')
            if node.is_empty():
                print('<i class="empty">', end='')
            print(node.form, end='')
            if node.is_empty():
                print('</i>', end='')
            if is_head:
                print('</b>', end='')

            while opened and opened[-1].words[-1] == node:
                if self.rtl:
                    print('</span></span>', end='')
                else:
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
                    self._start_subspan(broken, True)
                    opened.append(subspan)

            if not node.no_space_after:
                print(' ', end='')

        if not prev_node_mention:
            print('</span>', end='')
        print('</p>')

    def _is_head(self, node):
        for mention in node.coref_mentions:
            if mention.head == node:
                return mention
        return None


# id needs to be a valid DOM querySelector
# so it cannot contain [#./:] and maybe more,
# so let's substitute all [^\w\d-] to be on the safe side.
# DOM IDs cannot start with a digit, so prepend e.g. "n" if needed.
def _dom_esc(string):
    if string[0].isdecimal():
        string = 'n' + string
    return re.sub(r'[^\w\d-]', '_', string)

def _id(node):
    if node is None:
        return 'null'
    return _dom_esc(node.address())

def _esc(string):
    if string is None:
        string = ''
    return string.replace('\\', '\\\\').replace('"', r'\"')
