r"""Block ComplyWithText for adapting the nodes to comply with the text.

Implementation design details:
Usually, most of the inconsistencies between tree tokens and the raw text are simple to solve.
However, there may be also rare cases when it is not clear how to align the tokens
(nodes in the tree) with the raw text (stored in ``root.text``).
This block tries to solve the general case using several heuristics.

It starts with running a LCS-like algorithm (LCS = longest common subsequence)
``difflib.SequenceMatcher`` on the raw text and concatenation of tokens' forms,
i.e. on sequences of characters (as opposed to running LCS on sequences of tokens).

To prevent mis-alignment problems, we keep the spaces present in the raw text
and we insert spaces into the concatenated forms (``tree_chars``) according to ``SpaceAfter=No``.
An example of a mis-alignment problem:
text "énfase na necesidade" with 4 nodes "énfase en a necesidade"
should be solved by adding multiword token "na" over the nodes "en" and "a".
However, running LCS (or difflib) over the character sequences
"énfaseenanecesidade"
"énfasenanecesidade"
may result in énfase -> énfas.

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

    @staticmethod
    def allow_space(form):
        """Is space allowed within this token form?"""
        return re.fullmatch('[0-9 ]+([,.][0-9]+)?', form)

    @staticmethod
    def store_orig_form(node, new_form):
        """Store the original form of this node into MISC, unless the change is common&expected."""
        _ = new_form
        if node.form not in ("''", "``"):
            node.misc['OrigForm'] = node.form

    def process_tree(self, root):
        text = root.text
        if text is None:
            raise ValueError('Tree %s has no text, cannot use ud.ComplyWithText' % root)

        # Normalize the stored text (double space -> single space)
        # and skip sentences which are already ok.
        text = ' '.join(text.split())
        if text == root.compute_text():
            return

        tree_chars, char_nodes = _nodes_to_chars(root.token_descendants)

        # Align. difflib may not give LCS, but usually it is good enough.
        matcher = difflib.SequenceMatcher(None, tree_chars, text, autojunk=False)
        diffs = list(matcher.get_opcodes())
        _log_diffs(diffs, tree_chars, text, 'matcher')

        diffs = self.unspace_diffs(diffs, tree_chars, text)
        _log_diffs(diffs, tree_chars, text, 'unspace')

        diffs = self.merge_diffs(diffs, char_nodes)
        _log_diffs(diffs, tree_chars, text, 'merge')

        # Solve diffs.
        self.solve_diffs(diffs, tree_chars, char_nodes, text)

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

    def unspace_diffs(self, orig_diffs, tree_chars, text):
        diffs = []
        for diff in orig_diffs:
            edit, tree_lo, tree_hi, text_lo, text_hi = diff
            if edit != 'insert':
                if tree_chars[tree_lo] == ' ':
                    tree_lo += 1
                if tree_chars[tree_hi - 1] == ' ':
                    tree_hi -= 1
            old = tree_chars[tree_lo:tree_hi]
            new = text[text_lo:text_hi]
            if old == '' and new == '':
                continue
            elif old == new:
                edit = 'equal'
            elif old == '':
                edit = 'insert'
            diffs.append((edit, tree_lo, tree_hi, text_lo, text_hi))
        return diffs

    def merge_diffs(self, orig_diffs, char_nodes):
        """Make sure each diff starts on original token boundary.

        If not, merge the diff with the previous diff.
        E.g. (equal, "5", "5"), (replace, "-6", "–7")
        is changed into (replace, "5-6", "5–7")
        """
        diffs = []
        for diff in orig_diffs:
            edit, tree_lo, tree_hi, text_lo, text_hi = diff
            if edit != 'insert' and char_nodes[tree_lo] is not None:
                diffs.append(diff)
            elif edit == 'equal':
                while tree_lo < tree_hi and char_nodes[tree_lo] is None:
                    tree_lo += 1
                    text_lo += 1
                diffs[-1] = ('replace', diffs[-1][1], tree_lo, diffs[-1][3], text_lo)
                if tree_lo < tree_hi:
                    diffs.append(('equal', tree_lo, tree_hi, text_lo, text_hi))
            else:
                if not diffs:
                    diffs = [diff]
                elif diffs[-1][0] != 'equal':
                    diffs[-1] = ('replace', diffs[-1][1], tree_hi, diffs[-1][3], text_hi)
                else:
                    p_tree_hi = diffs[-1][2] - 1
                    p_text_hi = diffs[-1][4] - 1
                    while char_nodes[p_tree_hi] is None:
                        p_tree_hi -= 1
                        p_text_hi -= 1
                        assert p_tree_hi >= diffs[-1][1]
                        assert p_text_hi >= diffs[-1][3]
                    diffs[-1] = ('equal', diffs[-1][1], p_tree_hi, diffs[-1][3], p_text_hi)
                    diffs.append(('replace', p_tree_hi, tree_hi, p_text_hi, text_hi))
        return diffs

    def solve_diffs(self, diffs, tree_chars, char_nodes, text):
        for diff in diffs:
            edit, tree_lo, tree_hi, text_lo, text_hi = diff

            # Focus only on edits of type 'replace', log insertions and deletions as failures.
            if edit == 'equal':
                continue
            if edit in ('insert', 'delete'):
                logging.warning('Unable to solve token-vs-text mismatch\n%s',
                                _diff2str(diff, tree_chars, text))
                continue

            # Revert the splittng and solve the diff.
            nodes = [n for n in char_nodes[tree_lo:tree_hi] if n is not None]
            form = text[text_lo:text_hi]
            self.solve_diff(nodes, form.strip())

    def solve_diff(self, nodes, form):
        """Fix a given (minimal) tokens-vs-text inconsistency."""
        nodes_str = ' '.join([n.form for n in nodes])  # just for debugging
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
                    for split_form in reversed(forms[1:]):
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


def _nodes_to_chars(nodes):
    chars, char_nodes = [], []
    for node in nodes:
        form = node.form
        if node.misc['SpaceAfter'] != 'No' and node != nodes[-1]:
            form += ' '
        chars.extend(form)
        char_nodes.append(node)
        char_nodes.extend([None] * (len(form) - 1))
    return ''.join(chars), char_nodes


def _log_diffs(diffs, tree_chars, text, msg):
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        logging.warning('=== After %s:', msg)
        for diff in diffs:
            logging.warning(_diff2str(diff, tree_chars, text))


def _diff2str(diff, tree, text):
    old = '|' + ''.join(tree[diff[1]:diff[2]]) + '|'
    new = '|' + ''.join(text[diff[3]:diff[4]]) + '|'
    if diff[0] == 'equal':
        return '{:7} {!s:>50}'.format(diff[0], old)
    return '{:7} {!s:>50} --> {!s}'.format(diff[0], old, new)
