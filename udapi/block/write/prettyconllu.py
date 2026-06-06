"""PrettyConllu writer with aligned columns for plain-text, HTML and TeX/PDF.

The writer prints the 10 CoNLL-U columns (or their configurable subset) in
aligned columns. Column widths are configured by ``w_*`` parameters, but for
each sentence the effective width is shrunk to the longest value needed in
that sentence.

The main parameter is ``format`` which can be set to ``plain``, ``html`` or ``tex``.
``plain`` is the default and produces a plain text.
``html`` produces HTML output with tooltips.
``tex`` produces TeX/PDF output, one sentence per page (using \documentclass{standalone}).

The ``color`` parameter controls colorization in the output.
The default value is ``auto`` which means that for ``plain`` format,
colors are enabled only when writing to a TTY, while for ``html`` and ``tex`` formats,
colors are always enabled. Colors can be forced on or off with values ``1`` or ``0``.

Example CLI usage::

    # Plain text (default), compact per-sentence widths, no column names.
    udapy write.PrettyConllu < file.conllu

    # Plain text with custom widths and visible column names.
    udapy write.PrettyConllu print_column_names=1 w_form=20 w_feats=32 < file.conllu

    # Force color even if not writing to a TTY
    udapy write.PrettyConllu color=1 < file.conllu | less -R
    
    # The same as above, using a udapy syntactic sugar
    udapy -P < file.conllu | less -R

    # HTML output with tooltips.
    udapy write.PrettyConllu format=html < file.conllu > pretty.html

    # TeX/PDF output, one sentence per page (using \documentclass{standalone}).
    udapy write.PrettyConllu format=tex tex_style=standalone < file.conllu > pretty.tex
    pdflatex pretty.tex
"""
import os
import re
import sys
import textwrap
from html import escape

import colorama
from termcolor import colored

from udapi.block.write.conllu import Conllu

ATTRS_ALL = ('ord', 'form', 'lemma', 'upos', 'xpos', 'feats', 'head', 'deprel', 'deps', 'misc')
ANSI_COLOR_OF = {
    'ord': 'green',
    'form': 'yellow',
    'lemma': 'cyan',
    'upos': 'red',
    'xpos': 'white',
    'feats': 'magenta',
    'head': 'green',
    'deprel': 'blue',
    'deps': 'cyan',
    'misc': 'magenta',
}
HTML_COLOR_OF = {
    'ord': '#226622',
    'form': '#7a3e00',
    'lemma': '#5a2b8f',
    'upos': '#b00020',
    'xpos': '#4c4c4c',
    'feats': '#7a1ea1',
    'head': '#116611',
    'deprel': '#0a4fb5',
    'deps': '#0a7b7b',
    'misc': '#b24800',
}
TEX_COLOR_OF = {
    'ord': 'PrettyOrd',
    'form': 'PrettyForm',
    'lemma': 'PrettyLemma',
    'upos': 'PrettyUpos',
    'xpos': 'PrettyXpos',
    'feats': 'PrettyFeats',
    'head': 'PrettyHead',
    'deprel': 'PrettyDeprel',
    'deps': 'PrettyDeps',
    'misc': 'PrettyMisc',
}


class PrettyConllu(Conllu):
    """A writer of aligned CoNLL-U tables in plain, TeX and HTML formats."""

    def __init__(self, print_sent_id=True, print_text=True, print_empty_trees=True,
                 format='plain', attributes='ord,form,lemma,upos,xpos,feats,head,deprel,deps,misc',
                 w_ord=4, w_form=16, w_lemma=16, w_upos=8, w_xpos=10,
                 w_feats=28, w_head=6, w_deprel=16, w_deps=20, w_misc=28,
                 color='auto',
                 print_column_names=False,
                 tex_style='resize',
                 tooltip=True, tooltip_feats_misc=True,
                 mark='(ToDo|ToDoOrigText|Bug|Mark)', marked_only=False, **kwargs):
        """Create a new PrettyConllu writer.

        Args:
            print_sent_id: Print ``# sent_id = ...`` comments.
            print_text: Print ``# text = ...`` comments.
            print_empty_trees: Keep Conllu behavior for empty trees.
            format: Output format: ``plain``, ``tex`` or ``html``.
            attributes: Comma-separated list of displayed columns.
            w_ord: Max width for ``ord``.
            w_form: Max width for ``form``.
            w_lemma: Max width for ``lemma``.
            w_upos: Max width for ``upos``.
            w_xpos: Max width for ``xpos``.
            w_feats: Max width for ``feats``.
            w_head: Max width for ``head``.
            w_deprel: Max width for ``deprel``.
            w_deps: Max width for ``deps``.
            w_misc: Max width for ``misc``.
            color: Color mode ``auto``, ``1`` or ``0``.
                For ``plain``, ``auto`` enables colors only when writing to a TTY.
                For ``html`` and ``tex``, ``auto`` is interpreted as ``1``.
            print_column_names: Print column header row.
            tex_style: TeX rendering style:
                ``resize`` (default) shrinks too-wide tables to ``\textwidth``,
                ``standalone`` uses ``standalone`` class and puts each sentence
                on a new cropped page,
                ``overflow`` keeps natural width even if it overflows page.
            tooltip: Enable tooltip generation.
            tooltip_feats_misc: Show multiline tooltip for FEATS/MISC values with ``|``.
            mark: Regex for marked rows (same semantics as TextModeTrees).
            marked_only: Print only trees containing one or more marked nodes/comments.
        """
        super().__init__(print_sent_id=print_sent_id, print_text=print_text,
                         print_empty_trees=print_empty_trees, **kwargs)
        self.format = format
        self.attrs = [a.strip() for a in attributes.split(',') if a.strip()]
        unknown = [a for a in self.attrs if a not in ATTRS_ALL]
        if unknown:
            raise ValueError('Unknown attributes in PrettyConllu: %s' % ', '.join(unknown))

        self.width_of = {
            'ord': int(w_ord),
            'form': int(w_form),
            'lemma': int(w_lemma),
            'upos': int(w_upos),
            'xpos': int(w_xpos),
            'feats': int(w_feats),
            'head': int(w_head),
            'deprel': int(w_deprel),
            'deps': int(w_deps),
            'misc': int(w_misc),
        }
        self.tooltip = tooltip
        self.tooltip_feats_misc = tooltip_feats_misc
        self.color = color
        self._color_enabled = False
        self.print_column_names = print_column_names
        self.tex_style = tex_style
        self.marked_only = marked_only
        self.mark_re = re.compile(mark + '=') if mark else None
        self.comment_mark_re = re.compile(r'^\s*%s\s*=' % mark, re.M) if mark else None
        self._tex_sentence_count = 0

    def _collect_comment_lines(self, tree):
        """Collect comment lines (without leading #) for the current tree."""
        return list(self.iter_comment_lines(tree))

    def should_print_tree(self, tree, nodes):
        """Should this tree be printed?"""
        if not self.marked_only:
            return True
        if any(self.is_marked(node) for node in nodes):
            return True
        if self.comment_mark_re is None:
            return False
        comment_lines = self._collect_comment_lines(tree)
        if not comment_lines:
            return False
        comment_text = '\n'.join(comment_lines)
        return self.comment_mark_re.search(comment_text)

    def _print_comments_plain(self, tree):
        for line in self._collect_comment_lines(tree):
            print('#' + line)

    def before_process_document(self, document):
        """Initialize output wrappers and format-specific state."""
        super().before_process_document(document)
        if self.format == 'text':
            self.format = 'plain'

        if isinstance(self.color, str):
            color_mode = self.color.lower()
        elif isinstance(self.color, bool):
            color_mode = '1' if self.color else '0'
        else:
            color_mode = str(self.color)

        if color_mode == 'auto':
            self._color_enabled = sys.stdout.isatty() if self.format == 'plain' else True
        elif color_mode in ('1', 'true', 'yes', 'on'):
            self._color_enabled = True
        elif color_mode in ('0', 'false', 'no', 'off'):
            self._color_enabled = False
        else:
            raise ValueError("color must be one of: auto, 1, 0")

        if self.format == 'plain' and self._color_enabled:
            colorama.just_fix_windows_console()
            os.environ['FORCE_COLOR'] = '1'
        elif self.format == 'html':
            self._print_html_header()
        elif self.format == 'tex':
            if self.tex_style not in ('resize', 'standalone', 'overflow'):
                raise ValueError("tex_style must be one of: resize, standalone, overflow")
            self._tex_sentence_count = 0
            self._print_tex_header()
        elif self.format != 'plain':
            raise ValueError("format must be one of: plain, tex, html")

    def after_process_document(self, document):
        """Finalize output wrappers for html/tex formats."""
        if self.format == 'html':
            print('<pre class="sentence-gap">')
            print('')
            print('</pre>')
            print('</body>')
            print('</html>')
        elif self.format == 'tex':
            print('\\end{document}')
        super().after_process_document(document)

    def process_tree(self, tree):
        """Render one tree in the selected output format."""
        nodes = tree.descendants_and_empty
        if not nodes and not self.print_empty_trees:
            return
        if not self.should_print_tree(tree, nodes):
            return

        in_standalone_tex = self.format == 'tex' and self.tex_style == 'standalone'
        if in_standalone_tex:
            print('\\begin{mypage}')

        tex_comment_lines = []
        if self.format == 'plain':
            self._print_comments_plain(tree)
        elif self.format == 'html':
            self._print_comments_html(tree)
        else:
            tex_comment_lines = self._collect_comment_lines(tree)

        rows = self._build_rows(tree, nodes)
        widths = self._effective_widths(rows)
        if self.format == 'plain':
            if self._color_enabled:
                self._render_ansi(rows, widths)
            else:
                self._render_plain(rows, widths)
            print('')
        elif self.format == 'html':
            self._render_html(rows, widths)
        else:
            self._render_tex(rows, widths, tex_comment_lines)

        if in_standalone_tex:
            print('\\end{mypage}')

    def _effective_widths(self, rows):
        """Compute per-sentence effective widths from configured maxima."""
        widths = {}
        for attr in self.attrs:
            max_cfg = self.width_of[attr]
            if max_cfg <= 0:
                widths[attr] = 0
                continue
            max_len = 0
            for row in rows:
                text = '_' if row.get(attr) is None else str(row.get(attr))
                shown_len = min(len(text), max_cfg)
                if shown_len > max_len:
                    max_len = shown_len
            if self.print_column_names:
                max_len = max(max_len, min(len(attr.upper()), max_cfg))
            widths[attr] = min(max_cfg, max_len)
        return widths

    def _build_rows(self, tree, nodes):
        rows = []
        last_mwt_id = 0
        for node in nodes:
            mwt = node._mwt
            if mwt and node._ord > last_mwt_id:
                rows.append({
                    'ord': mwt.ord_range,
                    'form': '_' if mwt.form is None else mwt.form,
                    'lemma': '_',
                    'upos': '_',
                    'xpos': '_',
                    'feats': '_' if mwt._feats is None else str(mwt.feats),
                    'head': '_',
                    'deprel': '_',
                    'deps': '_',
                    'misc': '_' if mwt._misc is None else str(mwt.misc),
                    '_is_marked': False,
                    '_row_type': 'mwt',
                })
                last_mwt_id = mwt.words[-1]._ord

            if node._parent is None:
                head = '_'  # Empty nodes
            else:
                try:
                    head = str(node._parent._ord)
                except AttributeError:
                    head = '0'

            rows.append({
                'ord': str(node._ord),
                'form': node.form,
                'lemma': node.lemma,
                'upos': node.upos,
                'xpos': node.xpos,
                'feats': '_' if node._feats is None else str(node.feats),
                'head': head,
                'deprel': node.deprel,
                'deps': node.raw_deps,
                'misc': '_' if node._misc is None else str(node.misc),
                '_is_marked': self.is_marked(node),
                '_row_type': 'empty' if node._parent is None else 'token',
            })

        if not tree._descendants:
            rows.append({
                'ord': '1',
                'form': '_',
                'lemma': '_',
                'upos': '_',
                'xpos': '_',
                'feats': '_',
                'head': '0',
                'deprel': '_',
                'deps': '_',
                'misc': 'Empty=Yes',
                '_is_marked': False,
                '_row_type': 'artificial',
            })
        return rows

    def _render_plain(self, rows, widths):
        padded = {attr: w + 1 for attr, w in widths.items()}
        if self.print_column_names:
            print(self._header_line(padded))
            print(self._separator_line(padded))
        for row in rows:
            print(self._row_line(row, padded))

    def _render_ansi(self, rows, widths):
        padded = {attr: w + 1 for attr, w in widths.items()}
        if self.print_column_names:
            print(self._header_line(padded, colorize=True))
            print(self._separator_line(padded))
        for row in rows:
            print(self._row_line(row, padded, colorize=True))

    def _render_html(self, rows, widths):
        print('<table class="prettyconllu">')
        if self.print_column_names:
            print('  <thead><tr>%s</tr></thead>' % ''.join(
                '<th class="%s">%s</th>' % (attr, escape(attr.upper())) for attr in self.attrs))
        print('  <tbody>')
        for row in rows:
            row_class = row['_row_type'] + (' marked' if row['_is_marked'] else '')
            print('    <tr class="%s">' % row_class)
            for attr in self.attrs:
                full_text = '_' if row.get(attr) is None else str(row.get(attr))
                display, _, tip = self._fit_value(attr, row.get(attr), widths[attr], pad=False)
                value_html = escape(display)
                title_attr = ''
                if tip is not None:
                    tip_html = escape(tip).replace('\n', '&#10;')
                    title_attr = ' title="%s"' % tip_html

                if display != full_text:
                    full_html = escape(full_text)
                    value_html = '<span class="copy-full"%s>%s</span><span class="display-short">%s</span>' % (
                        title_attr, full_html, value_html)
                elif title_attr:
                    value_html = '<span%s>%s</span>' % (title_attr, value_html)
                print('      <td class="%s">%s</td>' % (attr, value_html))
            print('    </tr>')
        print('  </tbody>')
        print('</table>')
        # Keep one copyable blank line between sentences in browser text copy.
        print('<pre class="sentence-gap">')
        print('')
        print('</pre>')

    def _render_tex(self, rows, widths, comment_lines=None):
        self._tex_sentence_count += 1

        spec = ''.join(['r' if attr == 'head' else 'l' for attr in self.attrs])
        print('\\begingroup')
        print('\\small')
        print('\\noindent')
        if self.tex_style == 'resize':
            print('\\begin{adjustbox}{max width=\\textwidth}')
        print('\\begin{tabular}{%s}' % spec)
        if comment_lines:
            colspan = len(self.attrs)
            wrap_width = self._tex_comment_wrap_width(widths)
            for line in comment_lines:
                wrapped = self._wrap_tex_comment_line('#' + line, wrap_width)
                for part in wrapped:
                    comment = self._tex_escape(part)
                    if self._color_enabled:
                        content = '\\textcolor{gray}{\\ttfamily %s}' % comment
                    else:
                        content = '\\ttfamily %s' % comment
                    print('\\multicolumn{%d}{l}{%s} \\\\' % (colspan, content))
        if self.print_column_names:
            print('%s \\\\' % ' & '.join('\\textbf{%s}' % self._tex_escape(attr.upper()) for attr in self.attrs))
            print('\\hline')
        macro = {
            'ord': '\\OR',
            'form': '\\FO',
            'lemma': '\\LE',
            'upos': '\\UP',
            'xpos': '\\XP',
            'feats': '\\FE',
            'head': '\\HE',
            'deprel': '\\DE',
            'deps': '\\DP',
            'misc': '\\MI',
        }
        for row in rows:
            cells = []
            for attr in self.attrs:
                display, _, tip = self._fit_value(attr, row.get(attr), widths[attr], pad=False)
                text = self._tex_escape(display)
                if attr in ('feats', 'misc') and tip is not None:
                    text = '%s{%s}[%s]' % (macro[attr], text, self._tex_escape_tooltip(tip))
                elif attr in ('feats', 'misc'):
                    text = '%s{%s}' % (macro[attr], text)
                elif tip is not None:
                    text = '\\tooltip{%s}{%s}' % (text, self._tex_escape_tooltip(tip))
                    text = '%s{%s}' % (macro[attr], text)
                else:
                    text = '%s{%s}' % (macro[attr], text)
                cells.append(text)
            print('%s \\\\' % ' & '.join(cells))
        print('\\end{tabular}')
        if self.tex_style == 'resize':
            print('\\end{adjustbox}')
        print('\\endgroup')
        if self.tex_style != 'standalone':
            print('\\bigskip')
            print('')

    def _header_line(self, widths, colorize=False):
        parts = []
        for attr in self.attrs:
            width = widths[attr]
            head = self._fit_text(attr.upper(), width, align_right=(attr == 'head'))
            if colorize:
                head = self._colorize_ansi(attr, head, marked=False)
            parts.append(head)
        return '  '.join(parts)

    def _separator_line(self, widths):
        return '  '.join('-' * widths[attr] for attr in self.attrs)

    def _row_line(self, row, widths, colorize=False):
        parts = []
        marked = row['_is_marked']
        for attr in self.attrs:
            width = widths[attr]
            display, _, _ = self._fit_value(attr, row.get(attr), width, pad=True,
                                            align_right=(attr == 'head'))
            if colorize:
                display = self._colorize_ansi(attr, display, marked=marked)
            parts.append(display)
        return '  '.join(parts)

    def _fit_value(self, attr, value, width, pad=True, align_right=False):
        text = '_' if value is None else str(value)
        display, truncated = self._fit_text_with_flag(text, width, pad=pad, align_right=align_right)

        tip = None
        if self.tooltip:
            if truncated:
                tip = text
                if self.format == 'html' and attr in ('feats', 'misc') and '|' in text:
                    tip = text.replace('|', '\n')
            elif self.tooltip_feats_misc and attr in ('feats', 'misc') and '|' in text:
                tip = text if self.format == 'tex' else text.replace('|', '\n')
        return display, truncated, tip

    @staticmethod
    def _fit_text(text, width, align_right=False):
        return PrettyConllu._fit_text_with_flag(text, width, pad=True, align_right=align_right)[0]

    @staticmethod
    def _fit_text_with_flag(text, width, pad=True, align_right=False):
        if width <= 0:
            return '', False
        if len(text) <= width:
            if not pad:
                return text, False
            return (text.rjust(width) if align_right else text.ljust(width)), False
        if width <= 3:
            return ('.' * width), True
        return (text[:width - 3] + '...'), True

    def _print_comments_html(self, tree):
        lines = self._collect_comment_lines(tree)
        if not lines:
            return
        print('<pre class="comments">')
        for line in lines:
            print(escape('#' + line))
        print('</pre>')

    def is_marked(self, node):
        return self.mark_re.search(str(node.misc)) if self.mark_re is not None else False

    @staticmethod
    def _colorize_ansi(attr, value, marked=False):
        color = ANSI_COLOR_OF.get(attr)
        return colored(value, color, attrs=['reverse', 'bold'] if marked else None)

    @staticmethod
    def _tex_escape(value):
        replacements = {
            '\\': r'\textbackslash{}',
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\textasciicircum{}',
        }
        return ''.join(replacements.get(ch, ch) for ch in value)

    def _tex_comment_wrap_width(self, widths):
        # Approximate visible table width in monospace characters: sum of column
        # widths plus textual separators between columns.
        return max(24, sum(widths[attr] for attr in self.attrs) + 3 * (len(self.attrs) - 1))

    @staticmethod
    def _wrap_tex_comment_line(text, width):
        return textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False) or [text]

    def _tex_escape_tooltip(self, value):
        return self._tex_escape(value).replace('|', r'\string|')

    def _print_html_header(self):
        print('<!DOCTYPE html>')
        print('<html lang="en">')
        print('<head>')
        print('  <meta charset="utf-8">')
        print('  <title>PrettyConllu</title>')
        print('  <style>')
        print('    body { background: #ffffff; color: #222; font-family: "DejaVu Sans Mono", "Liberation Mono", monospace; margin: 16px; }')
        if self._color_enabled:
            print('    pre.comments { color: #4d4d4d; margin: 0 0 8px 0; }')
        else:
            print('    pre.comments { margin: 0 0 8px 0; }')
        print('    pre.sentence-gap { margin: 0 0 10px 0; line-height: 1; }')
        print('    table.prettyconllu { border-collapse: collapse; margin-bottom: 18px; }')
        print('    table.prettyconllu th, table.prettyconllu td { padding: 2px 8px; border: 1px solid #d8d8d8; white-space: pre; }')
        print('    table.prettyconllu td { position: relative; }')
        print('    table.prettyconllu td .copy-full { position: absolute; left: 8px; right: 8px; top: 2px; bottom: 2px; color: transparent; white-space: pre; user-select: text; overflow: hidden; }')
        print('    table.prettyconllu td .display-short { user-select: none; }')
        print('    table.prettyconllu th { background: #f5f5f5; }')
        if self._color_enabled:
            print('    table.prettyconllu tr.marked { background: #fff4cf; }')
        print('    table.prettyconllu td.head, table.prettyconllu th.head { text-align: right; }')
        if self._color_enabled:
            for attr, color in HTML_COLOR_OF.items():
                print('    table.prettyconllu .%s { color: %s; }' % (attr, color))
        print('  </style>')
        print('</head>')
        print('<body>')

    def _print_tex_header(self):
        if self.tex_style == 'standalone':
            print('\\documentclass[multi=mypage]{standalone}')
        else:
            print('\\documentclass[11pt]{article}')
            print('\\usepackage[margin=1.8cm]{geometry}')
        if self._color_enabled:
            print('\\usepackage[table]{xcolor}')
        if self.tex_style == 'resize':
            print('\\usepackage{adjustbox}')
        print('\\usepackage{pdfcomment}')
        print('\\usepackage{xparse}')
        print('\\usepackage[T1]{fontenc}')
        print('\\usepackage[utf8]{inputenc}')
        print('\\usepackage{textcomp}')
        print('\\setlength{\\parindent}{0pt}')
        print('\\newcommand{\\tooltip}[2]{\\pdftooltip{#1}{#2}}')
        print('\\newenvironment{mypage}{}{}')
        if self._color_enabled:
            print('\\def\\CL#1{\\noindent{\\color{gray}\\ttfamily #1}\\par}')
            print('\\def\\OR#1{\\textcolor{PrettyOrd}{#1}}')
            print('\\def\\FO#1{\\textcolor{PrettyForm}{#1}}')
            print('\\def\\LE#1{\\textcolor{PrettyLemma}{#1}}')
            print('\\def\\UP#1{\\textcolor{PrettyUpos}{#1}}')
            print('\\def\\XP#1{\\textcolor{PrettyXpos}{#1}}')
            print('\\NewDocumentCommand{\\FE}{m o}{\\textcolor{PrettyFeats}{\\IfNoValueTF{#2}{#1}{\\tooltip{#1}{#2}}}}')
            print('\\def\\HE#1{\\textcolor{PrettyHead}{#1}}')
            print('\\def\\DE#1{\\textcolor{PrettyDeprel}{#1}}')
            print('\\def\\DP#1{\\textcolor{PrettyDeps}{#1}}')
            print('\\NewDocumentCommand{\\MI}{m o}{\\textcolor{PrettyMisc}{\\IfNoValueTF{#2}{#1}{\\tooltip{#1}{#2}}}}')
            print('\\definecolor{PrettyOrd}{HTML}{226622}')
            print('\\definecolor{PrettyForm}{HTML}{7A3E00}')
            print('\\definecolor{PrettyLemma}{HTML}{5A2B8F}')
            print('\\definecolor{PrettyUpos}{HTML}{B00020}')
            print('\\definecolor{PrettyXpos}{HTML}{4C4C4C}')
            print('\\definecolor{PrettyFeats}{HTML}{7A1EA1}')
            print('\\definecolor{PrettyHead}{HTML}{116611}')
            print('\\definecolor{PrettyDeprel}{HTML}{0A4FB5}')
            print('\\definecolor{PrettyDeps}{HTML}{0A7B7B}')
            print('\\definecolor{PrettyMisc}{HTML}{B24800}')
        else:
            print('\\def\\CL#1{\\noindent{\\ttfamily #1}\\par}')
            print('\\def\\OR#1{#1}')
            print('\\def\\FO#1{#1}')
            print('\\def\\LE#1{#1}')
            print('\\def\\UP#1{#1}')
            print('\\def\\XP#1{#1}')
            print('\\NewDocumentCommand{\\FE}{m o}{\\IfNoValueTF{#2}{#1}{\\tooltip{#1}{#2}}}')
            print('\\def\\HE#1{#1}')
            print('\\def\\DE#1{#1}')
            print('\\def\\DP#1{#1}')
            print('\\NewDocumentCommand{\\MI}{m o}{\\IfNoValueTF{#2}{#1}{\\tooltip{#1}{#2}}}')
        print('\\begin{document}')
