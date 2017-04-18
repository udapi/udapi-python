r"""Block ComplyWithText for adapting the nodes to comply with the text.

Implementation design details:
Most of the inconsistencies between tree tokens and the raw text are simple to solve.
However, there may be also rare cases when it is not clear how to align the tokens
with the text. This block tries to solve the general case using several heuristics.

One possible implementation is to find the LCS (longest common subsequence)
of the raw text and concatenation of tokens' forms.
However, it is quite difficult to map these character-level diffs to token-level diffs
(one character-level diff may partially overlap with two tokens).

So this implementation starts with running a LCS-like algorithm (difflib) on a sequence of tokens
(instead of sequence of characters). Tokens from trees are obtain with `root.token_descendants`
(these tokens may be standard nodes for syntactic words or multi-word tokens).
From the raw text (`root.text`), we obtain "tokens" by splitting it on spaces and punctuation
(or more precisely any non-word character -- ``re.findall(r'\w+|[^\w\s]', string)``).
This tokenization is just approximate, to increase the chance of 1-1 alignment.
This heuristics does not work for languages written without spaces (e.g. Chinese, Japanese).

Author: Martin Popel
"""
import difflib
import logging
import re

from udapi.core.block import Block
from udapi.core.mwt import MWT


class ComplyWithText(Block):
    """Adapt the nodes to comply with the text."""

    def __init__(self, fix_text=True, prefer_mwt=True, allow_goeswith=True, max_mwt_length=4,
                 **kwargs):
        """Args:
        fix_text: After all heuristics are applied, the token forms may still not match the text.
            Should we edit the text to match the token forms (as a last resort)? Default=True.
        prefer_mwt - What to do if multiple subsequent nodes correspond to a text written
            without spaces and non-word characters (punctuation)?
            E.g. if "3pm doesn't" is annotated with four nodes "3 pm does n't".
            We can use either SpaceAfter=No, or create a multi-word token (MWT).
            Note that if there is space or punctuation, SpaceAfter=No will be used always
            (e.g. "3 p.m." annotated with three nodes "3 p. m.").
            If the character sequence does not match exactly, MWT will be used always
            (e.g. "3pm doesn't" annotated with four nodes "3 p.m. does not").
            Thus this parameter influences only the "unclear" cases.
            Default=True (i.e. prefer multi-word tokens over SpaceAfter=No).
        allow_goeswith - If a node corresponds to multiple space-separated strings in text,
            which are not allowed as tokens with space, we can either leave this diff
            unresolved or create new nodes and join them with the `goeswith` deprel.
            Default=True (i.e. add the goeswith nodes if applicable).
        max_mwt_length - Maximum length of newly created multi-word tokens (in syntactic words).
            Default=4.
        """
        super().__init__(**kwargs)
        self.fix_text = fix_text
        self.prefer_mwt = prefer_mwt
        self.allow_goeswith = allow_goeswith
        self.max_mwt_length = max_mwt_length

    def process_tree(self, root):
        text = root.text
        if text is None:
            raise ValueError('Tree %s has no text, cannot use ud.ComplyWithText' % root)

        # Normalize the stored text (double space -> single space)
        # and skip sentences which are already ok.
        text = ' '.join(text.split())
        if text == root.compute_text():
            return

        # To improve the 1-1 alignment, let's tokenize the text on spaces and punctuation.
        # We need to tokenize the token forms in the exactly same way, e.g. "5-6" -> "5" "-" "6".
        tree_nodes = root.token_descendants
        tree_forms = [t.form for t in tree_nodes]
        text_forms = text.split()
        tree_split_forms, tree_split_nodes = self.tokenize_list(tree_forms, tree_nodes)
        text_split_forms, text_split_nodes = self.tokenize_list(text_forms, text_forms)

        # Align. difflib does may not give LCS, but usually it is good enough.
        matcher = difflib.SequenceMatcher(None, tree_split_forms, text_split_forms, autojunk=False)
        diffs = list(matcher.get_opcodes())

        if logging.getLogger().isEnabledFor(logging.DEBUG):
            print('=== After matcher:')
            for diff in diffs:
                print(self.diff2str(diff, tree_split_forms, text_split_forms))

        # Make sure each diff starts on original token boundary.
        # If not, merge the diff with the previous diff.
        # E.g. (equal, ["5"], ["5"]), (replace, ["-","6"], ["–","7"])
        # is changed into (replace, ["5","-","6"], ["5","–","7"])
        for i, diff in enumerate(diffs):
            edit, tree_lo, tree_hi, text_lo, text_hi = diff

            if edit != 'insert' and tree_split_nodes[tree_lo] is None:
                if edit == 'equal':
                    while tree_lo < tree_hi and tree_split_nodes[tree_lo] is None:
                        tree_lo += 1
                        text_lo += 1
                    if tree_lo == tree_hi:
                        diffs[i] = ('ignore', 0, 0, 0, 0)
                    else:
                        diffs[i] = ('equal', tree_lo, tree_hi, text_lo, text_hi)
                    diffs[i - 1] = ('replace', diffs[i - 1][1], tree_lo, diffs[i - 1][3], text_lo)
                else:
                    prev_i = i - 1
                    while diffs[prev_i][0] == 'ignore':
                        prev_i -= 1
                    if diffs[prev_i][0] != 'equal':
                        diffs[prev_i] = ('replace', diffs[prev_i][1],
                                         tree_hi, diffs[prev_i][3], text_hi)
                        diffs[i] = ('ignore', 0, 0, 0, 0)
                    else:
                        p_tree_hi = diffs[prev_i][2] - 1
                        p_text_hi = diffs[prev_i][4] - 1
                        while tree_split_nodes[p_tree_hi] is None:
                            p_tree_hi -= 1
                            p_text_hi -= 1
                            assert p_tree_hi >= diffs[prev_i][1]
                            assert p_text_hi >= diffs[prev_i][3]
                        diffs[prev_i] = ('equal', diffs[prev_i][1], p_tree_hi,
                                         diffs[prev_i][3], p_text_hi)
                        diffs[i] = ('replace', p_tree_hi, tree_hi, p_text_hi, text_hi)

        if logging.getLogger().isEnabledFor(logging.DEBUG):
            print('=== After re-merging split tokens:')
            for diff in diffs:
                print(self.diff2str(diff, tree_split_forms, text_split_forms))

        # TODO split diffs if possible, e.g.
        # ['_', 'atenuación', '_', 'de', 'os'] --> ['_atenuación_', 'dos']
        # should be divided into two diffs:
        # ['_', 'atenuación', '_'] --> ['_atenuación_']
        # ['de', 'os'] --> ['dos']
        # This would probably need running another SequenceMatcher on characters
        # and then aligning the tokens/nodes.

        for diff in diffs:
            edit, tree_lo, tree_hi, text_lo, text_hi = diff

            # Focus only on edits of type 'replace', log insertions and deletions as failures.
            if edit in ('equal', 'ignore'):
                continue
            if edit in ('insert', 'delete'):
                logging.warning('Unable to solve token-vs-text mismatch\n%s',
                                self.diff2str(diff, tree_split_forms, text_split_forms))
                continue

            # Revert the splittng and solve the diff.
            nodes = [n for n in tree_split_nodes[tree_lo:tree_hi] if n is not None]
            form = text_split_forms[text_lo]
            for i in range(text_lo + 1, text_hi):
                if text_split_nodes[i] is not None:
                    form += ' '
                form += text_split_forms[i]
            self.solve_diff(nodes, form)

        # Fill SpaceAfter=No.
        tmp_text = text
        for node in root.token_descendants:
            if tmp_text.startswith(node.form):
                tmp_text = tmp_text[len(node.form):]
                if not tmp_text or tmp_text[0].isspace():
                    del node.misc['SpaceAfter']
                    tmp_text = tmp_text.lstrip()
                else:
                    node.misc['SpaceAfter'] = 'No'
            else:
                logging.warning('Node %s does not match text "%s"', node, tmp_text[:20])
                return

        # Edit root.text if needed.
        if self.fix_text:
            computed_text = root.compute_text()
            if text != computed_text:
                root.add_comment('ToDoOrigText = ' + root.text)
                root.text = computed_text

    def solve_diff(self, nodes, form):
        """Fix a given (minimal) tokens-vs-text inconsistency."""
        nodes_str = ' '.join([n.form for n in nodes])
        node = nodes[0]

        # First, solve the cases when the text contains a space.
        if ' ' in form:
            if len(nodes) == 1 and node.form == form.replace(' ', ''):
                if self.allow_space(form):
                    self.store_orig_form(node, form)
                    node.form = form
                elif self.allow_goeswith:
                    forms = form.split()
                    node.form = forms[0]
                    for split_form in reversed(form[1:]):
                        new = node.create_child(form=split_form, deprel='goeswith', upos=node.upos)
                        new.shift_after_node(node)
                else:
                    logging.warning('Unable to solve 1:m diff:\n%s -> %s', nodes_str, form)
            else:
                logging.warning('Unable to solve n:m diff:\n%s -> %s', nodes_str, form)

        # Second, solve the cases when multiple nodes match one form (without any spaces).
        elif len(nodes) > 1:
            # If the match is exact, we can choose between MWT ans SpaceAfter solutions.
            if not self.prefer_mwt and ''.join([n.form for n in nodes]) == form:
                pass  # SpaceAfter=No will be added later on.
            # If one of the nodes is already a MWT, we cannot have nested MWTs.
            # TODO: enlarge the MWT instead of failing.
            elif any(isinstance(n, MWT) for n in nodes):
                logging.warning('Unable to solve partial-MWT diff:\n%s -> %s', nodes_str, form)
            # MWT with too many words are suspicious.
            elif len(nodes) > self.max_mwt_length:
                logging.warning('Not creating too long (%d>%d) MWT:\n%s -> %s',
                                len(nodes), self.max_mwt_length, nodes_str, form)
            # Otherwise, create a new MWT.
            else:
                node.root.create_multiword_token(nodes, form)

        # Third, solve the 1-1 cases.
        else:
            self.store_orig_form(node, form)
            node.form = form

    def allow_space(self, form):
        return re.fullmatch('[0-9 ]+([,.][0-9]+)?', form)

    def store_orig_form(self, node, new_form):
        if node.form not in ("''", "``"):
            node.misc['OrigForm'] = node.form

    def tokenize_list(self, strings, nodes):
        new_strings = []
        new_nodes = []
        for string, node in zip(strings, nodes):
            new_nodes.append(node)
            substrings = self.tokenize(string)
            if len(substrings) > 1:
                new_strings.extend(substrings)
                new_nodes.extend([None] * (len(substrings) - 1))
            else:
                new_strings.append(string)
        return new_strings, new_nodes

    @staticmethod
    def tokenize(string):
        return re.findall(r'\w+|[^\w\s]', string)

    @staticmethod
    def diff2str(diff, tree, text):
        old = tree[diff[1]:diff[2]]
        new = text[diff[3]:diff[4]]
        return '{:7} {!r:>50} --> {!r}'.format(diff[0], old, new)
