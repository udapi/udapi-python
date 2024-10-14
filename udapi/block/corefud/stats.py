from udapi.core.block import Block
from collections import Counter

class Stats(Block):
    """Block corefud.Stats prints various coreference-related statistics."""

    def __init__(self, m_len_max=5, e_len_max=5,
                 report_basics=False, report_mentions=True, report_entities=True,
                 report_details=True, selected_upos='NOUN PRON PROPN DET ADJ VERB ADV NUM _',
                 exclude_singletons=False, exclude_nonsingletons=False, style='human',
                 per_doc=False, max_rows_per_page=50, docname='newdoc', docname_len=15,
                 **kwargs):
        super().__init__(**kwargs)
        self.m_len_max = m_len_max
        self.e_len_max = e_len_max
        self.report_basics = report_basics
        self.report_mentions = report_mentions
        self.report_entities = report_entities
        self.report_details = report_details
        self.exclude_singletons = exclude_singletons
        self.exclude_nonsingletons = exclude_nonsingletons
        self.style = style
        if style not in 'tex tex-table tex-doc human'.split():
            raise ValueError(f'Unknown style {style}')
        self.per_doc = per_doc
        self.max_rows_per_page = max_rows_per_page
        if docname not in 'newdoc filename'.split():
            raise ValueError(f'Unknown style {style}')
        self.docname = docname
        self.docname_len = docname_len
        self._header_printed = False
        self._lines_printed = None

        self.counter = Counter()
        self.mentions = 0
        self.entities = 0
        self.singletons = 0
        self.total_nodes = 0
        self.longest_mention = 0
        self.longest_entity = 0
        self.m_words = 0
        self.selected_upos = None if selected_upos == 'all' else selected_upos.split()

    def process_document(self, doc):
        self.total_nodes += len(list(doc.nodes))
        self.counter['documents'] += 1
        for entity in doc.coref_entities:
            len_mentions = len(entity.mentions)
            if len_mentions == 1:
                self.singletons += 1
            if len_mentions == 1 and self.exclude_singletons:
                continue
            elif len_mentions > 1 and self.exclude_nonsingletons:
                continue
            self.longest_entity = max(len_mentions, self.longest_entity)
            self.counter['c_total_len'] += len_mentions
            self.counter[f"c_len_{min(len_mentions, self.e_len_max)}"] += 1

            self.entities += 1
            if not self.report_mentions and not self.report_details:
                continue
            for mention in entity.mentions:
                self.mentions += 1
                all_words = len(mention.words)
                non_empty = len([w for w in mention.words if not w.is_empty()])
                self.m_words += all_words
                self.longest_mention = max(non_empty, self.longest_mention)
                self.counter['m_total_len'] += non_empty
                self.counter[f"m_len_{min(non_empty, self.m_len_max)}"] += 1
                if self.report_details:
                    upos = 'other'
                    if not self.selected_upos or mention.head.upos in self.selected_upos:
                        upos = mention.head.upos
                    self.counter['m_head_upos_' + upos] += 1
                    self.counter['m_with_empty'] += 1 if all_words > non_empty else 0
                    self.counter['m_with_gaps'] += 1 if ',' in mention.span else 0
                    heads, mwords = 0, set(mention.words)
                    for w in mention.words:
                        if w.parent:
                            heads += 0 if w.parent in mwords else 1
                        else:
                            heads += 0 if any(d['parent'] in mwords for d in w.deps) else 1
                    self.counter['m_nontreelet'] += 1 if heads > 1 else 0

        if self.report_basics:
            for tree in doc.trees:
                self.counter['newdocs'] += 1 if tree.newdoc else 0
                self.counter['sents'] += 1
                self.counter['words'] += len(tree.descendants)
                self.counter['empty'] += len(tree.empty_nodes)

    def after_process_document(self, doc):
        if self.per_doc:
            self.process_end(skip=False, doc=doc)
            self.counter = Counter()
            self.mentions = 0
            self.entities = 0
            self.singletons = 0
            self.total_nodes = 0
            self.longest_mention = 0
            self.longest_entity = 0
            self.m_words = 0

    def process_end(self, skip=True, doc=None):
        if not self._lines_printed:
            self.print_header()
            self._lines_printed = 0
        if self.per_doc:
            if skip:
                self.print_footer()
                return
            else:
                docname = doc.meta['loaded_from'] if self.docname == 'filename' else doc[0].trees[0].newdoc
                print(f"{docname:{self.docname_len}}", end='&' if self.style.startswith('tex') else '\n')
        elif self.style.startswith('tex-'):
            print(f"{self.counter['documents']:4} documents &")
        self._lines_printed += 1

        mentions_nonzero = 1 if self.mentions == 0 else self.mentions
        entities_nonzero = 1 if self.entities == 0 else self.entities
        total_nodes_nonzero = 1 if self.total_nodes == 0 else self.total_nodes

        columns =[ ]
        if self.report_basics:
            columns += [('docs', f"{self.counter['newdocs']:7,}"),
                        ('sents', f"{self.counter['sents']:7,}"),
                        ('words', f"{self.counter['words']:7,}"),
                        ('empty', f"{self.counter['empty']:7,}"),]
        if self.report_entities:
            columns += [('entities', f"{self.entities:7,}"),
                        ('entities_per1k', f"{1000 * self.entities / total_nodes_nonzero:6.0f}"),
                        ('longest_entity', f"{self.longest_entity:6}"),
                        ('avg_entity', f"{self.counter['c_total_len'] / entities_nonzero:5.1f}")]
            for i in range(1, self.e_len_max + 1):
                percent = 100 * self.counter[f"c_len_{i}"] / entities_nonzero
                columns.append((f"c_len_{i}{'' if i < self.e_len_max else '+'}", f"{percent:5.1f}"))
        if self.report_mentions:
            columns += [('mentions', f"{self.mentions:7,}"),
                        ('mentions_per1k', f"{1000 * self.mentions / total_nodes_nonzero:6.0f}"),
                        ('longest_mention', f"{self.longest_mention:6}"),
                        ('avg_mention', f"{self.counter['m_total_len'] / mentions_nonzero:5.1f}")]
            if self.m_len_max:
                for i in range(0, self.m_len_max + 1):
                    percent = 100 * self.counter[f"m_len_{i}"] / mentions_nonzero
                    columns.append((f"m_len_{i}{'' if i < self.m_len_max else '+'}", f"{percent:5.1f}"))
        if self.report_details:
            columns += [('with_empty', f"{100 * self.counter['m_with_empty'] / mentions_nonzero:5.1f}"),
                        ('with_gaps', f"{100 * self.counter['m_with_gaps'] / mentions_nonzero:5.1f}"),
                        ('nontreelet', f"{100 * self.counter['m_nontreelet'] / mentions_nonzero:5.1f}"),]
            if self.selected_upos:
                upos_list = self.selected_upos + ['other']
            else:
                upos_list = [x[12:] for x in self.counter if x.startswith('m_head_upos_')]
            for upos in upos_list:
                columns.append(('head_upos=' + upos, f"{100 * self.counter['m_head_upos_' + upos] / mentions_nonzero:5.1f}"))

        if self.style.startswith('tex'):
            print(" & ".join(c[1] for c in columns), end=" \\\\\n")
        elif self.style == 'human':
            for c in columns:
                print(f"{c[0]:>15} = {c[1].strip():>10}")
        if not self.per_doc:
            self.print_footer()
        elif self._lines_printed > self.max_rows_per_page:
            self.print_footer(False)
            self._lines_printed = 0

    def print_header(self):
        if not self.style.startswith('tex-'):
            return
        if self.style == 'tex-doc':
            if self._lines_printed is None:
                print(r'\documentclass[multi=mypage]{standalone}')
                print(r'\usepackage[utf8]{inputenc}\usepackage{booktabs}\usepackage{underscore}')
                print(r'\title{Udapi coreference statistics}')
                print(r'\begin{document}')
        print(r'\def\MC#1#2{\multicolumn{#1}{c}{#2}}')
        lines = [r'\begin{mypage}\begin{tabular}{@{}l ',
                 " " * self.docname_len,
                 ("document" if self.per_doc else "dataset ") + " " * (self.docname_len-8),
                 " " * self.docname_len]
        if self.report_basics:
            lines[0] += "rrrr "
            lines[1] += r'& \MC{4}{total number of}              '
            lines[2] += r'&        &         &         &         '
            lines[3] += r'&   docs &   sents &   words & empty n.'
        if self.report_entities:
            lines[0] += "rrrr "
            lines[1] += r'& \MC{4}{entities}                 '
            lines[2] += r'&  total & per 1k & \MC{2}{length} '
            lines[3] += r'&  count &  words &    max &  avg. '
            if self.e_len_max:
                for i in range(1, self.e_len_max + 1):
                    lines[0] += "r"
                    lines[2] += f"& {i:4}" + ("+ " if i==self.e_len_max else "  ")
                    lines[3] += r'&  [\%] '
                lines[0] += " "
                lines[1] += r'& \MC{' + str(self.e_len_max) + r'}{distribution of entity lengths}'
        if self.report_mentions:
            lines[0] += "rrrr "
            lines[1] += r'& \MC{4}{mentions}                  '
            lines[2] += r'&   total & per 1k & \MC{2}{length} '
            lines[3] += r'&   count &  words &    max &  avg. '
            if self.m_len_max:
                for i in range(0, self.m_len_max + 1):
                    lines[0] += "r"
                    lines[2] += f"& {i:4}" + ("+ " if i==self.m_len_max else "  ")
                    lines[3] += r'&  [\%] '
                lines[0] += " "
                lines[1] += r'& \MC{' + str(self.m_len_max + 1) + r'}{distribution of mention lengths}' + " "*7
        if self.report_details:
            lines[0] += "rrrr "
            lines[1] += r'& \MC{3}{mention type}       '
            lines[2] += r'&w/empty& w/gap&non-tree'
            lines[3] += r'&  [\%] ' * 3
            if self.selected_upos:
                upos_list = self.selected_upos + ['other']
            else:
                upos_list = [x[12:] for x in self.counter if x.startswith('m_head_upos_')]
            lines[0] += "@{~}r" * len(upos_list)
            lines[1] += r"& \MC{" + str(len(upos_list)) + r"}{distribution of head UPOS}"
            lines[2] += ''.join(f'&{upos:7}' for upos in upos_list)
            lines[3] += r'&  [\%] ' * len(upos_list)
        lines[0] += r'@{}}\toprule'
        last_col = 1
        lines[1] += r'\\'
        lines[2] += r'\\'
        lines[3] += r'\\\midrule'
        if self.report_basics:
            last_col += 4
            lines[1] += r'\cmidrule(lr){2-5}'
        if self.report_entities:
            lines[1] += r'\cmidrule(lr){' + f"{last_col+1}-{last_col+4}" + '}'
            lines[2] += r'\cmidrule(lr){' + f"{last_col+3}-{last_col+4}" + '}'
            last_col += 4
            if self.e_len_max:
                last_col += self.e_len_max
                lines[1] += r'\cmidrule(lr){6-' + str(last_col) + '}'
        if self.report_mentions:
            lines[1] += r'\cmidrule(lr){' + f"{last_col+1}-{last_col+4}" + '}'
            lines[2] += r'\cmidrule(lr){' + f"{last_col+3}-{last_col+4}" + '}'
            last_col += 4
            if self.m_len_max:
                lines[1] += r'\cmidrule(lr){' + f"{last_col+1}-{last_col+self.m_len_max+1}" + '}'
                last_col += self.m_len_max + 1
        if self.report_details:
            lines[1] += r'\cmidrule(lr){' + f"{last_col+1}-{last_col+3}"
            lines[1] += r'}\cmidrule(l){' + f"{last_col+4}-{last_col+3+len(upos_list)}" + '}'
        print("\n".join(lines))

    def print_footer(self, end_doc=True):
        if not self.style.startswith('tex-'):
            return
        print(r'\bottomrule\end{tabular}\end{mypage}')
        if self.style == 'tex-doc' and end_doc:
            print(r'\end{document}')
